#!/bin/bash

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Deploy Frontend to Google App Engine
# This script builds the React frontend and deploys it to Google App Engine as a static site

set -e

# Default configuration
DEFAULT_PROJECT_ID="qwiklabs-gcp-01-89519aa38551"
DEFAULT_REGION="us-central1"
DEFAULT_SERVICE_NAME="frontend"
DEFAULT_VERSION="v1"
DEFAULT_ENVIRONMENT="standard"
DEFAULT_RUNTIME="nodejs18"
DEFAULT_FRONTEND_DIR="frontend"
DEFAULT_BUILD_DIR="build"
DEFAULT_APP_YAML="app.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
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

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy the React frontend to Google App Engine

OPTIONS:
    -p, --project-id PROJECT_ID     Google Cloud Project ID (required)
    -r, --region REGION             Google Cloud region (default: $DEFAULT_REGION)
    -s, --service SERVICE_NAME      App Engine service name (default: $DEFAULT_SERVICE_NAME)
    -v, --version VERSION           App Engine version (default: $DEFAULT_VERSION)
    -e, --environment ENV           App Engine environment: standard|flexible (default: $DEFAULT_ENVIRONMENT)
    -t, --runtime RUNTIME           Runtime for flexible environment (default: $DEFAULT_RUNTIME)
    -f, --frontend-dir DIR          Frontend directory path (default: $DEFAULT_FRONTEND_DIR)
    -b, --build-dir DIR             Build output directory (default: $DEFAULT_BUILD_DIR)
    -y, --app-yaml FILE             App Engine configuration file (default: $DEFAULT_APP_YAML)
    -d, --dry-run                   Show what would be deployed without actually deploying
    -h, --help                      Show this help message

EXAMPLES:
    # Deploy with required project ID
    $0 --project-id my-gcp-project

    # Deploy to a specific region with custom service name
    $0 --project-id my-gcp-project --region europe-west1 --service my-frontend

    # Deploy using flexible environment
    $0 --project-id my-gcp-project --environment flexible --runtime nodejs18


    # Dry run to see what would be deployed
    $0 --project-id my-gcp-project --dry-run

REQUIREMENTS:
    - gcloud CLI installed and authenticated
    - Node.js and npm installed
    - App Engine API enabled in the target project

EOF
}

# Parse command line arguments
PROJECT_ID=""
REGION="$DEFAULT_REGION"
SERVICE_NAME="$DEFAULT_SERVICE_NAME"
VERSION="$DEFAULT_VERSION"
ENVIRONMENT="$DEFAULT_ENVIRONMENT"
RUNTIME="$DEFAULT_RUNTIME"
FRONTEND_DIR="$DEFAULT_FRONTEND_DIR"
BUILD_DIR="$DEFAULT_BUILD_DIR"
APP_YAML="$DEFAULT_FRONTEND_DIR/$DEFAULT_APP_YAML"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--runtime)
            RUNTIME="$2"
            shift 2
            ;;
        -f|--frontend-dir)
            FRONTEND_DIR="$2"
            shift 2
            ;;
        -b|--build-dir)
            BUILD_DIR="$2"
            shift 2
            ;;
        -y|--app-yaml)
            APP_YAML="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$PROJECT_ID" ]]; then
    print_error "Project ID is required. Use -p or --project-id to specify it."
    show_usage
    exit 1
fi

# Validate environment
if [[ "$ENVIRONMENT" != "standard" && "$ENVIRONMENT" != "flexible" ]]; then
    print_error "Environment must be either 'standard' or 'flexible'"
    exit 1
fi

# Check if frontend directory exists
if [[ ! -d "$FRONTEND_DIR" ]]; then
    print_error "Frontend directory '$FRONTEND_DIR' does not exist"
    exit 1
fi

# Check if package.json exists in frontend directory
if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
    print_error "package.json not found in frontend directory '$FRONTEND_DIR'"
    exit 1
fi

print_info "Starting frontend deployment to Google App Engine"
print_info "Project ID: $PROJECT_ID"
print_info "Region: $REGION"
print_info "Service: $SERVICE_NAME"
print_info "Version: $VERSION"
print_info "Environment: $ENVIRONMENT"
print_info "Frontend Directory: $FRONTEND_DIR"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "No active gcloud authentication found. Please run 'gcloud auth login'"
    exit 1
fi

# Set the project
print_info "Setting gcloud project to $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# Check if App Engine API is enabled
print_info "Checking if App Engine API is enabled..."
if ! gcloud services list --enabled --filter="name:appengine.googleapis.com" --format="value(name)" | grep -q "appengine.googleapis.com"; then
    print_warning "App Engine API is not enabled. Enabling it now..."
    gcloud services enable appengine.googleapis.com
fi

# Check if App Engine application exists, if not create it
print_info "Checking if App Engine application exists..."
if ! gcloud app describe --format="value(name)" 2>/dev/null | grep -q .; then
    print_info "Creating App Engine application in region $REGION..."
    gcloud app create --region="$REGION"
fi

# Check if app.yaml exists
if [[ ! -f "$APP_YAML" ]]; then
    print_error "App Engine configuration file not found: $APP_YAML"
    print_error "Please ensure the app.yaml file exists before deploying"
    exit 1
fi

print_info "Using App Engine configuration: $APP_YAML"

# Build the frontend
print_info "Building frontend..."
cd "$FRONTEND_DIR"

# Install dependencies if node_modules doesn't exist
if [[ ! -d "node_modules" ]]; then
    print_info "Installing npm dependencies..."
    npm install
fi

# Build the project
print_info "Running npm build..."
npm run build

# Check if build was successful
if [[ ! -d "$BUILD_DIR" ]]; then
    print_error "Build failed - $BUILD_DIR directory not found"
    exit 1
fi

print_success "Frontend build completed"

# Go back to the root directory
cd - > /dev/null

# For flexible environment, we need to create a simple server
if [[ "$ENVIRONMENT" == "flexible" ]]; then
    print_info "Creating server for flexible environment..."
    
    # Create a simple Node.js server for flexible environment
    cat > "server.js" << 'EOF'
const express = require('express');
const path = require('path');
const app = express();
const port = process.env.PORT || 8080;

// Serve static files from the build directory
app.use(express.static(path.join(__dirname, 'build')));

// Handle React routing, return all requests to React app
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
EOF

    # Create package.json for the server
    cat > "package.json" << EOF
{
  "name": "frontend-server",
  "version": "1.0.0",
  "description": "Server for React frontend on App Engine",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  },
  "engines": {
    "node": "18"
  }
}
EOF

    # Install express dependency
    print_info "Installing server dependencies..."
    npm install
fi

# Show what will be deployed
print_info "Files to be deployed:"
if [[ "$ENVIRONMENT" == "standard" ]]; then
    echo "  - $APP_YAML"
    echo "  - $FRONTEND_DIR/$BUILD_DIR/ (static files)"
else
    echo "  - $APP_YAML"
    echo "  - server.js"
    echo "  - package.json"
    echo "  - $FRONTEND_DIR/$BUILD_DIR/ (static files)"
fi

# Deploy to App Engine
if [[ "$DRY_RUN" == true ]]; then
    print_warning "DRY RUN - No actual deployment will be performed"
    print_info "Would deploy to: https://$VERSION-dot-$SERVICE_NAME-dot-$PROJECT_ID.appspot.com"
    exit 0
fi

print_info "Deploying to App Engine..."
if [[ "$ENVIRONMENT" == "standard" ]]; then
    # For standard environment, we need to copy files to the right structure
    # Create a temporary deployment directory
    DEPLOY_DIR=$(mktemp -d)
    print_info "Creating deployment structure in $DEPLOY_DIR"
    
    # Copy the app.yaml to the deployment directory
    cp "$APP_YAML" "$DEPLOY_DIR/"
    
    # Copy the build directory to the deployment directory
    cp -r "$FRONTEND_DIR/$BUILD_DIR" "$DEPLOY_DIR/"
    
    # Deploy from the deployment directory
    cd "$DEPLOY_DIR"
    gcloud app deploy app.yaml --version="$VERSION" --quiet
    
    # Clean up the temporary directory
    cd - > /dev/null
    rm -rf "$DEPLOY_DIR"
else
    # For flexible environment, deploy from the root directory
    gcloud app deploy "$APP_YAML" --version="$VERSION" --quiet
fi

# Get the deployed URL
DEPLOYED_URL="https://$VERSION-dot-$SERVICE_NAME-dot-$PROJECT_ID.appspot.com"
print_success "Deployment completed successfully!"
print_success "Your frontend is available at: $DEPLOYED_URL"

# Clean up temporary files for flexible environment
if [[ "$ENVIRONMENT" == "flexible" ]]; then
    print_info "Cleaning up temporary server files..."
    rm -f server.js package.json package-lock.json
    rm -rf node_modules
fi

print_info "Deployment script completed!"
