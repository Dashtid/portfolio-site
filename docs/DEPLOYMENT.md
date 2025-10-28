# Production Deployment Guide

This guide covers deploying the Portfolio Migration project to production using Vercel (frontend) and Fly.io (backend).

## Overview

**Architecture**:
- Frontend: Vercel (FREE tier) - Static Vue 3 build with CDN
- Backend: Fly.io (\/month) - FastAPI container with PostgreSQL
- Total Cost: \/usr/bin/bash-5/month

**URLs**:
- Frontend Production: https://dashti.se (custom domain) or https://your-project.vercel.app
- Backend Production: https://dashti-portfolio-backend.fly.dev
- Old Site: https://dashti.se (Azure Static Web Apps - will be replaced)

---

## Prerequisites

1. **Accounts**:
   - [Vercel account](https://vercel.com/signup) (free)
   - [Fly.io account](https://fly.io/app/sign-up) (credit card required for \/month plan)
   - GitHub account (for CI/CD)

2. **CLI Tools**:
   3. **Domain**:
   - dashti.se domain (currently pointing to Azure)
   - Will be updated to point to Vercel

---

## Backend Deployment (Fly.io)

### Step 1: Install Fly.io CLI

### Step 2: Login to Fly.io

This opens a browser for authentication.

### Step 3: Create Fly.io App

**Configuration prompts**:
- App name: \ (or press Enter for auto-generated)
- Region: Choose \ (Stockholm, Sweden - closest to you)
- PostgreSQL: \ (select Development configuration, \/usr/bin/bash/month for small DB)
- Deploy now: \ (we'''ll configure secrets first)

This creates \ (already created in this repo).

### Step 4: Set Environment Variables

Last Updated: 2025-10-28
