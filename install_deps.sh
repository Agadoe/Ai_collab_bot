#!/bin/bash
set -e

# Update system packages
apt-get update

# Install build dependencies
apt-get install -y \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    pkg-config

# Upgrade pip and install build tools
pip install --upgrade pip setuptools wheel

# Install build dependencies first
pip install -r requirements-build.txt

# Install main dependencies
pip install -r requirements.txt

# Clean up
apt-get remove -y \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    pkg-config
apt-get autoremove -y
rm -rf /var/lib/apt/lists/*

echo "Dependencies installed successfully!"