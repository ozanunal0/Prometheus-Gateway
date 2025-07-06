#!/bin/bash
# Manual deployment script for MkDocs to GitHub Pages

set -e

echo "🚀 Deploying Prometheus Gateway Documentation to GitHub Pages"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if we have uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled"
        exit 1
    fi
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install/update dependencies
echo "📦 Installing MkDocs dependencies..."
pip install -q mkdocs mkdocs-material mkdocs-mermaid2-plugin

# Build documentation
echo "🔨 Building documentation..."
mkdocs build --clean --strict

# Deploy to GitHub Pages
echo "🚀 Deploying to GitHub Pages..."
mkdocs gh-deploy --clean --message "Deploy documentation {sha} with MkDocs {version}"

echo "✅ Documentation deployed successfully!"
echo "📖 Your documentation should be available at:"
echo "   https://ozanunal0.github.io/Prometheus-Gateway/"
echo ""
echo "📝 Note: It may take a few minutes for changes to appear."