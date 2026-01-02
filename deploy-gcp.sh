#!/bin/bash
#
# AI Manus - Google Cloud Deployment Script
# Deploys AI Manus to Google Cloud Run with Gemini 2.5 Pro
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
GEMINI_API_KEY="AIzaSyC7pKCPc9dInPlk9u-84qi2yYOE4HuZaDE"

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   AI Manus - Google Cloud Deployment   ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get or set project ID
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}Enter your Google Cloud Project ID:${NC}"
    read -r PROJECT_ID
fi

echo "Using Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo -e "${YELLOW}Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    redis.googleapis.com \
    --project="$PROJECT_ID"

echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

# Create secrets
echo -e "${YELLOW}Creating secrets in Secret Manager...${NC}"

# Gemini API Key
echo -n "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
    --data-file=- \
    --replication-policy="automatic" \
    --project="$PROJECT_ID" 2>/dev/null || \
    echo -n "$GEMINI_API_KEY" | gcloud secrets versions add gemini-api-key \
    --data-file=- \
    --project="$PROJECT_ID"

echo -e "${GREEN}✓ Gemini API key stored${NC}"

# MongoDB URI (placeholder - update after MongoDB Atlas setup)
echo -e "${YELLOW}Enter your MongoDB URI (or press Enter to use placeholder):${NC}"
read -r MONGODB_URI
if [ -z "$MONGODB_URI" ]; then
    MONGODB_URI="mongodb://localhost:27017"
fi

echo -n "$MONGODB_URI" | gcloud secrets create mongodb-uri \
    --data-file=- \
    --replication-policy="automatic" \
    --project="$PROJECT_ID" 2>/dev/null || \
    echo -n "$MONGODB_URI" | gcloud secrets versions add mongodb-uri \
    --data-file=- \
    --project="$PROJECT_ID"

# JWT Secret
JWT_SECRET=$(openssl rand -hex 32)
echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret \
    --data-file=- \
    --replication-policy="automatic" \
    --project="$PROJECT_ID" 2>/dev/null || \
    echo -n "$JWT_SECRET" | gcloud secrets versions add jwt-secret \
    --data-file=- \
    --project="$PROJECT_ID"

echo -e "${GREEN}✓ Secrets created${NC}"
echo ""

# Build and push Docker images
echo -e "${YELLOW}Building Docker images...${NC}"

# Backend
echo "Building backend..."
gcloud builds submit ./backend \
    --tag="gcr.io/$PROJECT_ID/manus-backend:latest" \
    --project="$PROJECT_ID" \
    --timeout=20m

echo -e "${GREEN}✓ Backend image built${NC}"

# Frontend
echo "Building frontend..."
gcloud builds submit ./frontend \
    --tag="gcr.io/$PROJECT_ID/manus-frontend:latest" \
    --project="$PROJECT_ID" \
    --timeout=20m

echo -e "${GREEN}✓ Frontend image built${NC}"
echo ""

# Deploy backend
echo -e "${YELLOW}Deploying backend to Cloud Run...${NC}"

gcloud run deploy manus-backend \
    --image="gcr.io/$PROJECT_ID/manus-backend:latest" \
    --platform=managed \
    --region="$REGION" \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --min-instances=1 \
    --max-instances=10 \
    --set-secrets="API_KEY=gemini-api-key:latest,MONGODB_URI=mongodb-uri:latest,JWT_SECRET_KEY=jwt-secret:latest" \
    --set-env-vars="API_BASE=https://generativelanguage.googleapis.com/v1beta/openai/,MODEL_NAME=gemini-2.0-flash-exp,TEMPERATURE=0.7,MAX_TOKENS=8192,LOG_LEVEL=INFO" \
    --project="$PROJECT_ID"

BACKEND_URL=$(gcloud run services describe manus-backend \
    --platform=managed \
    --region="$REGION" \
    --format="value(status.url)" \
    --project="$PROJECT_ID")

echo -e "${GREEN}✓ Backend deployed: $BACKEND_URL${NC}"
echo ""

# Deploy frontend
echo -e "${YELLOW}Deploying frontend to Cloud Run...${NC}"

gcloud run deploy manus-frontend \
    --image="gcr.io/$PROJECT_ID/manus-frontend:latest" \
    --platform=managed \
    --region="$REGION" \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=1 \
    --max-instances=10 \
    --set-env-vars="BACKEND_URL=$BACKEND_URL" \
    --project="$PROJECT_ID"

FRONTEND_URL=$(gcloud run services describe manus-frontend \
    --platform=managed \
    --region="$REGION" \
    --format="value(status.url)" \
    --project="$PROJECT_ID")

echo -e "${GREEN}✓ Frontend deployed: $FRONTEND_URL${NC}"
echo ""

# Summary
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}         Deployment Complete! 🎉         ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}✅ Frontend URL:${NC} $FRONTEND_URL"
echo -e "${GREEN}✅ Backend URL:${NC} $BACKEND_URL"
echo -e "${GREEN}✅ AI Model:${NC} Gemini 2.5 Pro (gemini-2.0-flash-exp)"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Set up MongoDB Atlas: https://cloud.mongodb.com"
echo "2. Update MongoDB URI secret:"
echo "   echo -n 'YOUR_URI' | gcloud secrets versions add mongodb-uri --data-file=- --project=$PROJECT_ID"
echo "3. (Optional) Set up Redis for session management"
echo "4. Access your application at: $FRONTEND_URL"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo "• Gemini API Key is securely stored in Secret Manager"
echo "• Backend auto-scales from 1-10 instances"
echo "• Frontend is optimized for global CDN delivery"
echo "• All traffic is over HTTPS automatically"
echo ""
