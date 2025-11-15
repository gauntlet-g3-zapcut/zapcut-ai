# AdCraft AI

AI-powered video ad generation platform that creates 4K video ads with music using Sora, Suno, and OpenAI.

## Features

- 🎨 **Brand Management**: Create and manage brands with product images
- 💬 **Conversational Brief**: Chat with AI Creative Director to define ad style
- 🎬 **Video Generation**: Generate 4K video ads with 5 scenes
- 🎵 **Music Generation**: Create matching soundtracks with precise timing
- 📱 **Simple UI**: Clean, modern interface inspired by AdCreative.ai and Adobe GenStudio

## Tech Stack

### Frontend
- React (Vite)
- React Router
- Firebase Auth
- Tailwind CSS (or styled-components)

### Backend
- FastAPI (Python)
- PostgreSQL
- Celery + Redis
- OpenAI (GPT-4)
- Replicate (Sora, Suno, Image Generation)
- FFmpeg
- AWS S3

## Quick Setup

```bash
# Install dependencies
cd frontend && npm install
cd ../backend && pip install -r requirements.txt

# Setup environment variables
cp frontend/.env.example frontend/.env.local
cp backend/.env.example backend/.env
# Edit .env files with your API keys

# Run database migrations
cd backend && alembic upgrade head

# Start services (3 terminals)
# Terminal 1: Backend API
cd backend && uvicorn app.main:app --reload

# Terminal 2: Celery Worker
cd backend && celery -A app.celery_app worker --loglevel=info

# Terminal 3: Frontend
cd frontend && npm run dev
```

## Detailed Setup

See [SETUP.md](./SETUP.md) for:
- Prerequisites installation
- API keys setup (Firebase, OpenAI, Replicate, AWS)
- Database configuration
- Production deployment
- Troubleshooting

## Environment Variables

Required API keys:
- **Firebase** - Authentication
- **OpenAI** - GPT-4 for Creative Director
- **Replicate** - Sora (video), Suno (music), image generation
- **AWS S3** - Video storage

See `.env.example` files in `frontend/` and `backend/` directories.

## Project Structure

```
adcraft/
├── frontend/          # React frontend
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/    # SQLAlchemy models
│   │   ├── api/       # API routes
│   │   ├── services/  # Business logic
│   │   └── tasks/     # Celery tasks
│   └── alembic/       # Database migrations
├── PRD.md            # Product Requirements Document
└── tasks.md          # Development tasks
```

## Development

See `tasks.md` for detailed development tasks and timeline.

## Deployment

- **Frontend**: https://adcraft-blond.vercel.app/
- **Backend**: Deploy to Railway (see [DEPLOYMENT.md](./DEPLOYMENT.md))

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment guide.

## License

MIT


