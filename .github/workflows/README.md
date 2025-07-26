# GitHub Actions Setup

## Required Secrets

To enable automated deployments, you need to set up the following secrets in your GitHub repository:

### Render Secrets
1. **RENDER_API_KEY**: 
   - Go to Render Dashboard → Account Settings → API Keys
   - Create a new API key
   - Add it as a GitHub secret

2. **RENDER_SERVICE_ID**:
   - Go to your Render service dashboard
   - The service ID is in the URL: `https://dashboard.render.com/web/srv-[SERVICE_ID]`
   - Add it as a GitHub secret

### Vercel Secrets
1. **VERCEL_TOKEN**:
   - Go to Vercel Dashboard → Account Settings → Tokens
   - Create a new token
   - Add it as a GitHub secret

2. **VERCEL_ORG_ID**:
   - Run `vercel whoami` in your project directory
   - Or find it in `.vercel/project.json` after running `vercel link`

3. **VERCEL_PROJECT_ID**:
   - Find it in `.vercel/project.json` after running `vercel link`
   - Or in your Vercel project settings

## Adding Secrets to GitHub

1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret with its corresponding value

## Workflows

- **CI**: Runs on every push and pull request
- **Deploy**: Automatically deploys to Render and Vercel on push to main
- **Dependency Update**: Weekly check for outdated dependencies