# 🎬 Zapcut AI

> AI-powered video ad generation platform that transforms creative production from hours to minutes

## ✨ What is Zapcut AI?

Zapcut AI is an end-to-end video ad creation pipeline that combines conversational AI, automated asset generation, and intelligent video composition. Create professional video advertisements through simple natural language conversations - no creative expertise required! 🚀

## 🏗️ Project Structure

```
zapcut-ai/
├── 🎨 frontend/          # Electron desktop app (React + TypeScript)
├── 🌐 website/           # Marketing website (React + Vite)
├── ⚙️  backend/          # FastAPI server (Python)
├── 🗄️  database/         # Database migrations & schemas
└── 📚 docs/              # Project documentation
```

## 🚀 Quick Start

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Website Setup
```bash
cd website
npm install
npm run dev
```

## 🛠️ Tech Stack

- **Frontend:** React + TypeScript + Electron + TailwindCSS
- **Backend:** Python + FastAPI + PostgreSQL + Redis
- **AI Services:** OpenAI GPT-4, Sora (Replicate), Suno AI
- **Storage:** AWS S3 / Supabase Storage
- **Deployment:** Fly.io, Railway, Vercel

## 🎯 Key Features

- 💬 **Conversational Interface** - AI guides you through strategic questions
- 📝 **Script Generation** - GPT-4 creates detailed video scripts
- 🎥 **Video Production** - Sora & Veo generates high-quality scenes
- 🎤 **Professional Audio** - Voiceover + custom music composition
- ✂️ **Full Editing Control** - Generated videos load into Zapcut editor

## 📖 Documentation

- [Project Overview](docs/project-overview.md)
- [Epic Documentation](docs/epics/)
- [Technical Architecture](docs/plans/AIVP_TechnicalArchitecture.md)

## 🚢 Deployment

See deployment guides:
- [Backend Deployment](backend/DEPLOY.md)
- [Quick Deploy Guide](backend/QUICK_DEPLOY.md)

## 📝 License

[Add your license here]

---

**Status:** 🟢 Active Development | **Version:** MVP

