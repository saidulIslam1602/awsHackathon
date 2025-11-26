#!/usr/bin/env python3
"""
Setup script for Privacy Policy Assistant
Hackathon: AWS Experience North GenAI 2025
"""

import os
import subprocess
import sys

def check_python_version():
    """Ensure Python 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_requirements():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

def setup_environment():
    """Create environment file if it doesn't exist"""
    env_file = ".env"
    if not os.path.exists(env_file):
        print("🔧 Creating environment file...")
        env_content = """# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=eu-north-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Optional: Debug mode
DEBUG=False
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Created {env_file} - please add your AWS credentials")
    else:
        print(f"✅ {env_file} already exists")

def test_installation():
    """Test basic imports"""
    print("🧪 Testing installation...")
    try:
        import streamlit
        import boto3
        import plotly
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)

def main():
    """Main setup process"""
    print("🚀 Setting up Privacy Policy Assistant")
    print("=" * 50)
    
    check_python_version()
    install_requirements()
    setup_environment()
    test_installation()
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Add your AWS credentials to .env file")
    print("2. Run: streamlit run app.py")
    print("3. Open browser to http://localhost:8501")
    print("\n🏆 Good luck at the hackathon!")

if __name__ == "__main__":
    main()
