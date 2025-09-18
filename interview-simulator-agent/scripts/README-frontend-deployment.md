# Frontend Deployment to Google App Engine

This directory contains scripts and configurations for deploying the React frontend to Google App Engine as a static site.

## Overview

The deployment script (`deploy-frontend-appengine.sh`) builds the React frontend and deploys it to Google App Engine. This is separate from the main application deployment which uses Google Cloud Run.

## Prerequisites

1. **Google Cloud CLI**: Install and authenticate with `gcloud`
   ```bash
   # Install gcloud CLI (if not already installed)
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   
   # Authenticate
   gcloud auth login
   ```

2. **Node.js and npm**: Required for building the frontend
   ```bash
   # Check if installed
   node --version
   npm --version
   ```

3. **App Engine API**: The script will enable this automatically, but you can enable it manually:
   ```bash
   gcloud services enable appengine.googleapis.com
   ```

## Quick Start

### Basic Deployment

```bash
# Deploy with your project ID
./scripts/deploy-frontend-appengine.sh --project-id YOUR_GCP_PROJECT_ID
```

### Advanced Usage

```bash
# Deploy to a specific region with custom service name
./scripts/deploy-frontend-appengine.sh \
  --project-id my-gcp-project \
  --region europe-west1 \
  --service my-frontend \
  --version v2

# Deploy using flexible environment
./scripts/deploy-frontend-appengine.sh \
  --project-id my-gcp-project \
  --environment flexible \
  --runtime nodejs18

# Create app.yaml and deploy
./scripts/deploy-frontend-appengine.sh \
  --project-id my-gcp-project \
  --create-app-yaml

# Dry run to see what would be deployed
./scripts/deploy-frontend-appengine.sh \
  --project-id my-gcp-project \
  --dry-run
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project-id` | Google Cloud Project ID | Required |
| `--region` | Google Cloud region | `us-central1` |
| `--service` | App Engine service name | `frontend` |
| `--version` | App Engine version | `v1` |
| `--environment` | App Engine environment | `standard` |
| `--runtime` | Runtime for flexible environment | `nodejs18` |
| `--frontend-dir` | Frontend directory path | `frontend` |
| `--build-dir` | Build output directory | `build` |
| `--app-yaml` | App Engine config file | `app.yaml` |
| `--create-app-yaml` | Create app.yaml if missing | `false` |
| `--dry-run` | Show what would be deployed | `false` |

## App Engine Environments

### Standard Environment (Default)
- **Pros**: Faster cold starts, automatic scaling, simpler configuration
- **Cons**: Limited to specific runtimes, less control over infrastructure
- **Best for**: Static sites, simple applications

### Flexible Environment
- **Pros**: Full control over runtime, custom Docker images, persistent disks
- **Cons**: Slower cold starts, more complex configuration
- **Best for**: Complex applications, custom requirements

## File Structure

```
interview-simulator-agent/
├── app.yaml                    # App Engine configuration
├── scripts/
│   ├── deploy-frontend-appengine.sh  # Deployment script
│   └── README-frontend-deployment.md # This file
└── frontend/
    ├── package.json
    ├── src/
    └── build/                  # Generated during deployment
```

## Deployment Process

1. **Validation**: Checks prerequisites and parameters
2. **Build**: Runs `npm install` and `npm run build` in frontend directory
3. **Configuration**: Creates or uses existing `app.yaml`
4. **Deployment**: Deploys to App Engine using `gcloud app deploy`
5. **Cleanup**: Removes temporary files (for flexible environment)

## Accessing Your Deployed Frontend

After successful deployment, your frontend will be available at:
```
https://VERSION-dot-SERVICE-dot-PROJECT_ID.appspot.com
```

For example:
```
https://v1-dot-frontend-dot-my-project.appspot.com
```

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **App Engine API Not Enabled**
   ```bash
   gcloud services enable appengine.googleapis.com
   ```

3. **Build Failures**
   - Check Node.js version compatibility
   - Ensure all dependencies are in `package.json`
   - Run `npm install` manually in frontend directory

4. **Deployment Failures**
   - Check project permissions
   - Verify App Engine application exists
   - Review `app.yaml` syntax

### Debug Mode

Run with `--dry-run` to see what would be deployed without actually deploying:

```bash
./scripts/deploy-frontend-appengine.sh --project-id my-project --dry-run
```

## Integration with CI/CD

You can integrate this script into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Deploy Frontend to App Engine
  run: |
    ./scripts/deploy-frontend-appengine.sh \
      --project-id ${{ secrets.GCP_PROJECT_ID }} \
      --version ${{ github.sha }}
```

## Security Considerations

- The script uses HTTPS by default (`secure: always`)
- Environment variables are set to production mode
- Static files are served with appropriate headers
- Consider using App Engine's built-in security features

## Cost Optimization

- **Standard Environment**: Pay per request, good for low traffic
- **Flexible Environment**: Pay per instance, better for high traffic
- Use `--dry-run` to test configurations before deploying
- Monitor usage in Google Cloud Console

## Support

For issues with the deployment script:
1. Check the troubleshooting section above
2. Review Google App Engine documentation
3. Check the script's help: `./scripts/deploy-frontend-appengine.sh --help`
