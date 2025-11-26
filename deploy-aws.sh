#!/bin/bash

# AWS Deployment Script for Privacy Policy Analyzer
# AWS Hackathon 2025

set -e

echo "🚀 AWS Privacy Policy Analyzer Deployment"
echo "=========================================="

# Configuration
APP_NAME="privacy-policy-analyzer"
REGION="us-west-2"
CLUSTER_NAME="${APP_NAME}-cluster"
SERVICE_NAME="${APP_NAME}-service"
TASK_FAMILY="${APP_NAME}-task"
ECR_REPO="${APP_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install Docker first."
    exit 1
fi

print_status "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured or invalid."
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_success "AWS Account ID: $ACCOUNT_ID"

# Step 1: Create ECR Repository
print_status "Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPO --region $REGION &> /dev/null || {
    print_status "Creating new ECR repository: $ECR_REPO"
    aws ecr create-repository --repository-name $ECR_REPO --region $REGION
    print_success "ECR repository created"
}

# Step 2: Build and Push Docker Image
print_status "Building Docker image..."
docker build -t $APP_NAME .

print_status "Tagging image for ECR..."
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO"
docker tag $APP_NAME:latest $ECR_URI:latest

print_status "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI

print_status "Pushing image to ECR..."
docker push $ECR_URI:latest
print_success "Image pushed to ECR: $ECR_URI:latest"

# Step 3: Create ECS Cluster
print_status "Creating ECS cluster..."
aws ecs describe-clusters --clusters $CLUSTER_NAME --region $REGION &> /dev/null || {
    print_status "Creating new ECS cluster: $CLUSTER_NAME"
    aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $REGION
    print_success "ECS cluster created"
}

# Step 4: Create Task Definition
print_status "Creating ECS task definition..."
cat > task-definition.json << EOF
{
    "family": "$TASK_FAMILY",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "512",
    "memory": "1024",
    "executionRoleArn": "arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "$APP_NAME",
            "image": "$ECR_URI:latest",
            "portMappings": [
                {
                    "containerPort": 8501,
                    "protocol": "tcp"
                },
                {
                    "containerPort": 8502,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {
                    "name": "AWS_DEFAULT_REGION",
                    "value": "$REGION"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/$APP_NAME",
                    "awslogs-region": "$REGION",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "essential": true
        }
    ]
}
EOF

# Create CloudWatch log group
aws logs create-log-group --log-group-name "/ecs/$APP_NAME" --region $REGION 2>/dev/null || true

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $REGION
print_success "Task definition registered"

# Step 5: Create Security Group
print_status "Creating security group..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region $REGION)
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name "${APP_NAME}-sg" \
    --description "Security group for Privacy Policy Analyzer" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query 'GroupId' \
    --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${APP_NAME}-sg" \
    --query 'SecurityGroups[0].GroupId' \
    --output text \
    --region $REGION)

# Add inbound rules
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 8501 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || true

aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 8502 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || true

print_success "Security group configured: $SECURITY_GROUP_ID"

# Step 6: Get Subnets
print_status "Getting subnet information..."
SUBNETS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=default-for-az,Values=true" \
    --query 'Subnets[*].SubnetId' \
    --output text \
    --region $REGION | tr '\t' ',')

print_success "Using subnets: $SUBNETS"

# Step 7: Create ECS Service
print_status "Creating ECS service..."
aws ecs create-service \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --task-definition $TASK_FAMILY \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
    --region $REGION 2>/dev/null || {
    print_warning "Service might already exist, updating..."
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --region $REGION
}

print_success "ECS service created/updated"

# Step 8: Wait for deployment
print_status "Waiting for service to become stable..."
aws ecs wait services-stable --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION

# Step 9: Get public IP
print_status "Getting public IP address..."
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --query 'taskArns[0]' --output text --region $REGION)
ENI_ID=$(aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks $TASK_ARN --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text --region $REGION)
PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --query 'NetworkInterfaces[0].Association.PublicIp' --output text --region $REGION)

# Clean up temporary files
rm -f task-definition.json

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
print_success "Application URL: http://$PUBLIC_IP:8501"
print_success "API Endpoint: http://$PUBLIC_IP:8502"
print_success "Cluster: $CLUSTER_NAME"
print_success "Service: $SERVICE_NAME"
print_success "Region: $REGION"

echo ""
print_warning "Note: It may take a few minutes for the application to fully start."
print_warning "Browser extension will need to be updated to use the new API endpoint."

echo ""
echo "🔧 Useful Commands:"
echo "aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION"
echo "aws logs tail /ecs/$APP_NAME --follow --region $REGION"
echo ""
