# Portfolio Migration - Complete Setup Guide

## Repository Information
- **GitHub URL**: https://github.com/Dashtid/portfolio-migration
- **Type**: Private Repository
- **Stack**: Vue 3 + FastAPI + SQLAlchemy

## GitHub Secrets Required for Deployment

For GitHub Actions and Azure deployment, you'll need to set these secrets in your repository:

### Required Secrets
1. **AZURE_STATIC_WEB_APPS_API_TOKEN**
   - Get from Azure Portal after creating Static Web App
   - Settings → Secrets and variables → Actions → New repository secret

2. **GITHUB_CLIENT_ID**
   - Your GitHub OAuth App Client ID
   - Already configured in your .env file

3. **GITHUB_CLIENT_SECRET**
   - Your GitHub OAuth App Client Secret
   - Already configured in your .env file

4. **JWT_SECRET_KEY**
   - Your JWT secret for token generation
   - Already configured in your .env file

## Setting Up GitHub Secrets

```bash
# Using GitHub CLI (gh)
gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --repo Dashtid/portfolio-migration
gh secret set GITHUB_CLIENT_ID --repo Dashtid/portfolio-migration
gh secret set GITHUB_CLIENT_SECRET --repo Dashtid/portfolio-migration
gh secret set JWT_SECRET_KEY --repo Dashtid/portfolio-migration
```

Or manually via GitHub UI:
1. Go to https://github.com/Dashtid/portfolio-migration/settings/secrets/actions
2. Click "New repository secret" for each secret
3. Add the name and value

## Local Development URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/api/docs
- **Admin Panel**: http://localhost:3000/admin

## Current Running Services

You have the following services running:
- Backend on port 8000 (multiple instances - may need cleanup)
- Backend on port 8001 (main development instance)
- Frontend development server on port 3000

## Quick Commands

### Stop all running backend servers
```bash
# Windows
taskkill /F /IM python.exe
```

### Restart backend
```bash
cd backend
source venv/Scripts/activate
uvicorn app.main:app --reload --port 8001
```

### Restart frontend
```bash
cd frontend
npm run dev
```

## Next Steps

1. **Clean up running processes**: You have multiple backend instances running
2. **Set up GitHub secrets** for CI/CD if planning to deploy
3. **Configure Azure Static Web Apps** if deploying to Azure
4. **Add content** through the admin panel
5. **Customize** the portfolio content to match your needs

## Project Structure

```
portfolio-migration/
├── backend/           # FastAPI backend
│   ├── app/          # Application code
│   ├── tests/        # Test files
│   └── venv/         # Python virtual environment
├── frontend/         # Vue 3 frontend
│   ├── src/          # Source code
│   ├── public/       # Static assets
│   └── node_modules/ # Dependencies
├── .github/          # GitHub Actions workflows
├── docker-compose.yml # Docker configuration
└── README.md         # Project documentation
```

## Repository Features

- [+] Git initialized and connected to GitHub
- [+] Comprehensive .gitignore configured
- [+] Initial commit with all project files
- [+] GitHub Actions workflow for CI/CD
- [+] Docker support for containerization
- [+] Azure deployment configuration
- [+] PWA support with service worker

## Troubleshooting

### Multiple backend servers running
```bash
# Check what's using the ports
netstat -ano | findstr :8000
netstat -ano | findstr :8001

# Kill specific process
taskkill /PID [process_id] /F
```

### Frontend not loading
- Check if backend is running on correct port (8001)
- Verify CORS settings in backend
- Clear browser cache

### Authentication issues
- Verify GitHub OAuth credentials in .env
- Check callback URL matches GitHub OAuth app settings
- Ensure JWT_SECRET_KEY is set

## Support

For issues or questions:
- Check the README.md for basic setup
- Review DEPLOYMENT.md for deployment guidance
- Check API docs at http://localhost:8001/api/docs