# AdCraft AI - Setup Guide

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **PostgreSQL** 14+
- **Redis** 6+
- **FFmpeg** 4+

## Quick Start

### 1. Clone and Install

```bash
# Clone the repository
git clone <your-repo-url>
cd adcraft

# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Environment Variables

#### Frontend (.env)

```bash
cd frontend
cp .env.example .env.local
```

Edit `.env.local` with your Firebase configuration:

```env
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abc123
VITE_API_URL=http://localhost:8000
```

#### Backend (.env)

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/adcraft

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxx

# Replicate
REPLICATE_API_TOKEN=r8_xxxxx

# AWS S3
AWS_ACCESS_KEY_ID=AKIAXXXXX
AWS_SECRET_ACCESS_KEY=xxxxx
AWS_S3_BUCKET=adcraft-videos
AWS_REGION=us-east-1

# Firebase Admin SDK
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nxxxxx\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com

# API
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. Setup Services

#### PostgreSQL Database

```bash
# Create database
createdb adcraft

# Or using psql
psql -U postgres
CREATE DATABASE adcraft;
\q
```

#### Redis

```bash
# macOS (with Homebrew)
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis

# Windows
# Download from https://redis.io/download
```

#### FFmpeg

```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### 4. Run Database Migrations

```bash
cd backend
alembic upgrade head
```

### 5. Start Development Servers

#### Terminal 1: Backend API

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2: Celery Worker

```bash
cd backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info
```

#### Terminal 3: Frontend

```bash
cd frontend
npm run dev
```

The app will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## API Keys Setup

### 1. Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Authentication (Email/Password and Google)
4. Get Web App config from Project Settings
5. Generate Service Account key for Admin SDK

### 2. OpenAI

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an API key
3. Ensure you have access to GPT-4

### 3. Replicate

1. Go to [Replicate](https://replicate.com/)
2. Create an account
3. Get API token from Account Settings
4. Note: Sora might not be publicly available yet - check Replicate for alternatives

### 4. AWS S3

1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Create an S3 bucket (e.g., `adcraft-videos`)
3. Create IAM user with S3 permissions
4. Generate access key and secret

## Production Deployment

### Railway (Backend)

1. Create Railway account
2. Create new project
3. Add PostgreSQL service
4. Add Redis service
5. Add Web service (connect to GitHub)
6. Set environment variables
7. Deploy

### Vercel (Frontend)

1. Create Vercel account
2. Import GitHub repository
3. Set environment variables
4. Deploy

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Check connection
psql -U postgres -d adcraft
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping
# Should return: PONG
```

### Module Import Errors

```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt --force-reinstall
```

### CORS Errors

Make sure `CORS_ORIGINS` in backend `.env` includes your frontend URL.

## Development Tips

- Use PostgreSQL GUI: [pgAdmin](https://www.pgadmin.org/) or [Postico](https://eggerapps.at/postico/)
- Use Redis GUI: [RedisInsight](https://redis.com/redis-enterprise/redis-insight/)
- Monitor Celery tasks with [Flower](https://flower.readthedocs.io/)
- Test API with FastAPI docs at `/docs`

## Need Help?

- Check `tasks.md` for development roadmap
- Check `PRD.md` for product specifications
- Open an issue on GitHub

