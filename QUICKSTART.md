# AdCraft AI - Quick Start Guide

## 🚀 Get Running in 10 Minutes

### Step 1: Prerequisites (5 min)

Install these if you don't have them:

```bash
# macOS
brew install node python@3.11 postgresql@14 redis ffmpeg

# Start services
brew services start postgresql
brew services start redis
```

### Step 2: Clone & Install (2 min)

```bash
# Clone
git clone <your-repo-url>
cd adcraft

# Frontend
cd frontend
npm install

# Backend
cd ../backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Environment Variables (2 min)

#### Backend: `backend/.env`

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/adcraft
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-your-key-here
REPLICATE_API_TOKEN=r8_your-token-here
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_S3_BUCKET=your-bucket
AWS_REGION=us-east-1
FIREBASE_PROJECT_ID=your-project
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour-key\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-email@project.iam.gserviceaccount.com
CORS_ORIGINS=http://localhost:5173
```

#### Frontend: `frontend/.env.local`

```env
VITE_FIREBASE_API_KEY=your-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456:web:abc123
VITE_API_URL=http://localhost:8000
```

### Step 4: Database Setup (1 min)

```bash
# Create database
createdb adcraft

# Run migrations
cd backend
alembic upgrade head
```

### Step 5: Start Everything (3 terminals)

```bash
# Terminal 1: Backend API
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Celery Worker
cd backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info

# Terminal 3: Frontend
cd frontend
npm run dev
```

### Step 6: Open & Test

1. Open http://localhost:5173
2. Click "Get Started"
3. Sign up with email/password
4. Create your first brand!

## 🔑 Where to Get API Keys

### Firebase (Free)
1. https://console.firebase.google.com/
2. Create project → Enable Auth → Get config

### OpenAI ($20 credit)
1. https://platform.openai.com/
2. Create account → API Keys → Create

### Replicate (Pay-as-you-go)
1. https://replicate.com/
2. Sign up → Account → API Tokens

### AWS S3 (Free tier)
1. https://console.aws.amazon.com/
2. Create bucket → IAM user → Access key

## 📞 Need Help?

- **Full setup**: See `SETUP.md`
- **Architecture**: See `PRD.md`
- **Status**: See `STATUS.md`
- **Issues**: Open GitHub issue

## 🎯 Test the Full Flow

1. **Sign Up** → Create account
2. **Create Brand** → "Luxury Coffee Maker" + 2 images
3. **Chat** → "I want a modern, energetic ad"
4. **Answer Questions** → Style, audience, etc.
5. **Review** → See 5-scene storyline
6. **Generate** → Wait 3-5 minutes
7. **Watch** → Your 4K video ad!

---

**Time to first video**: ~10 minutes setup + 5 minutes generation = **15 minutes total**

