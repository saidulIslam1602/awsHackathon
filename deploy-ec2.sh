#!/bin/bash

# Simple EC2 Deployment Script for Privacy Policy Analyzer
# AWS Hackathon 2025

set -e

echo "🚀 EC2 Privacy Policy Analyzer Deployment"
echo "=========================================="

# Configuration
APP_NAME="privacy-policy-analyzer"
REGION="us-west-2"
INSTANCE_TYPE="t3.micro"
KEY_NAME="hackathon-key"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_status "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured or invalid."
    exit 1
fi

# Step 1: Create Key Pair (if not exists)
print_status "Creating key pair..."
aws ec2 describe-key-pairs --key-names $KEY_NAME --region $REGION &> /dev/null || {
    print_status "Creating new key pair: $KEY_NAME"
    aws ec2 create-key-pair --key-name $KEY_NAME --region $REGION --query 'KeyMaterial' --output text > ${KEY_NAME}.pem
    chmod 400 ${KEY_NAME}.pem
    print_success "Key pair created: ${KEY_NAME}.pem"
}

# Step 2: Create Security Group
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
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || true

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

# Step 3: Create User Data Script
cat > user-data.sh << 'EOF'
#!/bin/bash
yum update -y
yum install -y docker git python3 python3-pip

# Start Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone and setup application
cd /home/ec2-user
git clone https://github.com/your-repo/privacy-policy-analyzer.git || {
    # If no git repo, we'll copy files manually
    mkdir -p privacy-policy-analyzer
    cd privacy-policy-analyzer
}

# Install Python dependencies
pip3 install streamlit boto3 flask flask-cors requests beautifulsoup4 pandas pillow

# Create systemd service
cat > /etc/systemd/system/privacy-analyzer.service << 'EOFSERVICE'
[Unit]
Description=Privacy Policy Analyzer
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/privacy-policy-analyzer
Environment=AWS_DEFAULT_REGION=us-west-2
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOFSERVICE

systemctl daemon-reload
systemctl enable privacy-analyzer
EOF

# Step 4: Launch EC2 Instance
print_status "Launching EC2 instance..."
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" "Name=state,Values=available" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text \
    --region $REGION)

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --count 1 \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP_ID \
    --user-data file://user-data.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$APP_NAME}]" \
    --region $REGION \
    --query 'Instances[0].InstanceId' \
    --output text)

print_success "Instance launched: $INSTANCE_ID"

# Step 5: Wait for instance to be running
print_status "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Step 6: Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text \
    --region $REGION)

# Clean up
rm -f user-data.sh

echo ""
echo "🎉 EC2 Deployment Complete!"
echo "=========================="
print_success "Instance ID: $INSTANCE_ID"
print_success "Public IP: $PUBLIC_IP"
print_success "SSH Command: ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
print_success "Application URL: http://$PUBLIC_IP:8501 (after setup completes)"
print_success "API Endpoint: http://$PUBLIC_IP:8502"

echo ""
print_warning "Note: The application is still setting up. Wait 5-10 minutes before accessing."
print_warning "You'll need to manually copy your application files to the instance."

echo ""
echo "🔧 Next Steps:"
echo "1. Copy your application files:"
echo "   scp -i ${KEY_NAME}.pem -r . ec2-user@$PUBLIC_IP:~/privacy-policy-analyzer/"
echo ""
echo "2. SSH into the instance and start the service:"
echo "   ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
echo "   sudo systemctl start privacy-analyzer"
echo ""
echo "3. Update browser extension API endpoint to: http://$PUBLIC_IP:8502"
echo ""
