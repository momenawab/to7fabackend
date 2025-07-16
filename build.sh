#!/bin/bash

# Build script for Railway deployment
echo "🚀 Starting Railway build process..."

# Check Python version
echo "🐍 Python version:"
python --version || python3 --version

# Set Python command
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Upgrade pip
echo "📦 Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip

# Install requirements with specific flags for Railway
echo "📦 Installing Python dependencies..."
$PYTHON_CMD -m pip install --no-cache-dir --prefer-binary -r requirements.txt

# Collect static files
echo "📦 Collecting static files..."
$PYTHON_CMD manage.py collectstatic --noinput

echo "✅ Build completed successfully!" 