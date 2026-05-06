#!/bin/bash

# Deploy Script - IIIbrasil to Production
# Usage: ./scripts/deploy.sh [render|aws|manual]

set -e

DEPLOY_TARGET="${1:-render}"
ENVIRONMENT="production"
VERSION=$(git describe --tags --always 2>/dev/null || echo "unknown")

echo "🚀 Starting deployment to $DEPLOY_TARGET"
echo "📌 Version: $VERSION"
echo "🕐 Time: $(date)"

# Validate environment
echo "✓ Validating environment..."

if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found!"
    echo "   Copy .env.example to .env and configure variables"
    exit 1
fi

# Load environment
set -a
source .env
set +a

# Pre-deployment checks
echo "✓ Running pre-deployment checks..."

# Check if on main branch
if [ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then
    read -p "⚠️  Not on main branch. Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
fi

# Check if working directory is clean
if [ ! -z "$(git status --porcelain)" ]; then
    echo "❌ ERROR: Working directory has uncommitted changes"
    echo "   Commit or stash your changes first"
    exit 1
fi

# Test build locally
echo "✓ Testing build..."
cd backend && pip install -r requirements.txt > /dev/null 2>&1 && cd ..
cd frontend && npm ci > /dev/null 2>&1 && npm run build > /dev/null 2>&1 && cd ..

# Deploy based on target
case "$DEPLOY_TARGET" in
    render)
        echo "🎯 Deploying to Render..."
        
        # Validate Render configuration
        if [ -z "$RENDER_DEPLOY_HOOK_BACKEND" ] || [ -z "$RENDER_API_KEY" ]; then
            echo "❌ ERROR: RENDER_DEPLOY_HOOK_BACKEND or RENDER_API_KEY not set"
            exit 1
        fi
        
        # Push to main to trigger Render deployment
        echo "📤 Pushing to main branch..."
        git push origin main
        
        echo "✅ Pushed to main. Render will automatically deploy."
        echo "📊 Monitor deployment at: https://dashboard.render.com"
        ;;
        
    aws)
        echo "🎯 Deploying to AWS..."
        
        # Check AWS CLI
        if ! command -v aws &> /dev/null; then
            echo "❌ ERROR: AWS CLI not found"
            echo "   Install via: pip install awscli"
            exit 1
        fi
        
        # Build and push Docker images
        echo "📦 Building Docker images..."
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        REGISTRY="$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com"
        
        # Login to ECR
        aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $REGISTRY
        
        # Backend
        echo "🐳 Building backend image..."
        docker build -f backend/Dockerfile -t $REGISTRY/ebrasil-backend:$VERSION backend/
        docker push $REGISTRY/ebrasil-backend:$VERSION
        docker tag $REGISTRY/ebrasil-backend:$VERSION $REGISTRY/ebrasil-backend:latest
        docker push $REGISTRY/ebrasil-backend:latest
        
        # Frontend
        echo "🐳 Building frontend image..."
        docker build -f frontend/Dockerfile -t $REGISTRY/ebrasil-frontend:$VERSION frontend/
        docker push $REGISTRY/ebrasil-frontend:$VERSION
        docker tag $REGISTRY/ebrasil-frontend:$VERSION $REGISTRY/ebrasil-frontend:latest
        docker push $REGISTRY/ebrasil-frontend:latest
        
        echo "✅ Images pushed to ECR"
        echo "📊 Update ECS task definitions with new image tags"
        ;;
        
    manual)
        echo "🎯 Manual deployment..."
        echo "📋 Steps:"
        echo "  1. Review changes: git diff origin/main"
        echo "  2. Merge: git merge origin/main"
        echo "  3. Deploy: docker-compose -f docker-compose.prod.yml up -d"
        ;;
        
    *)
        echo "❌ Unknown deploy target: $DEPLOY_TARGET"
        echo "   Available: render, aws, manual"
        exit 1
        ;;
esac

# Post-deployment health check
echo "⏳ Waiting for service to be ready..."
sleep 10

API_URL="${PRODUCTION_API_URL:-https://ebrasil-backend.onrender.com}"
HEALTH_CHECK="$API_URL/health"

for i in {1..30}; do
    if curl -f "$HEALTH_CHECK" > /dev/null 2>&1; then
        echo "✅ Service is healthy!"
        echo "🌐 API: $API_URL"
        echo "📊 Docs: $API_URL/docs"
        exit 0
    fi
    echo "⏳ Checking... ($i/30)"
    sleep 2
done

echo "⚠️  Health check failed. Service may be starting."
echo "🔗 Check logs at your deployment platform dashboard"

exit 0
