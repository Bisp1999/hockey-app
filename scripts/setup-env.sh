#!/bin/bash
# Environment setup script for Hockey Pickup Manager

set -e

echo "🏒 Hockey Pickup Manager - Environment Setup"
echo "============================================="

# Function to create directory if it doesn't exist
create_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo "✅ Created directory: $1"
    fi
}

# Function to copy env file if it doesn't exist
setup_env_file() {
    local env_file="$1"
    local example_file="$2"
    
    if [ ! -f "$env_file" ]; then
        if [ -f "$example_file" ]; then
            cp "$example_file" "$env_file"
            echo "✅ Created $env_file from $example_file"
        else
            echo "⚠️  Warning: $example_file not found"
        fi
    else
        echo "ℹ️  $env_file already exists"
    fi
}

# Create necessary directories
echo "📁 Creating directories..."
create_dir "logs"
create_dir "uploads"
create_dir "test_uploads"
create_dir "instance"

# Set up environment files
echo "🔧 Setting up environment files..."
setup_env_file ".env" ".env.example"
setup_env_file ".env.local" ".env.example"

# Frontend environment setup
echo "🌐 Setting up frontend environment..."
cd frontend
setup_env_file ".env" ".env.development"
setup_env_file ".env.local" ".env.development"
cd ..

# Set permissions
echo "🔒 Setting permissions..."
chmod +x scripts/*.sh 2>/dev/null || true
chmod 755 logs uploads test_uploads instance 2>/dev/null || true

# Generate secret key if needed
if [ ! -f ".env.local" ] || ! grep -q "SECRET_KEY=" ".env.local"; then
    echo "🔑 Generating secret key..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "SECRET_KEY=$SECRET_KEY" >> .env.local
    echo "✅ Secret key generated and added to .env.local"
fi

echo ""
echo "🎉 Environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Review and customize .env.local with your settings"
echo "2. Review and customize frontend/.env.local with your settings"
echo "3. Start the development environment with: make up"
echo ""
echo "🔍 Important files created/configured:"
echo "   - .env.local (local environment overrides)"
echo "   - frontend/.env.local (frontend local overrides)"
echo "   - logs/ (application logs directory)"
echo "   - uploads/ (file uploads directory)"
echo "   - instance/ (Flask instance directory)"
echo ""
