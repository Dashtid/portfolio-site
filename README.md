# Portfolio Website - Vue 3 + FastAPI

A modern, dynamic portfolio website built with Vue 3 frontend and FastAPI backend, featuring GitHub OAuth authentication and content management.

## Features

- **Dynamic Portfolio**: Showcase experience, education, projects with Stockholm-themed design  
- **Admin Panel**: Manage content through authenticated admin interface
- **GitHub OAuth**: Secure authentication using GitHub credentials
- **Responsive Design**: Bootstrap 5.3.3 with custom styling
- **Modern Stack**: Vue 3 with Composition API, FastAPI with async SQLAlchemy

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/api/docs
