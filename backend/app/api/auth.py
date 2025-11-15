from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
from app.database import get_db
from app.models.user import User
from sqlalchemy.orm import Session
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

# Initialize Firebase Admin
try:
    if settings.FIREBASE_PROJECT_ID and settings.FIREBASE_PRIVATE_KEY and settings.FIREBASE_CLIENT_EMAIL:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": settings.FIREBASE_PROJECT_ID,
            "private_key": settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n") if isinstance(settings.FIREBASE_PRIVATE_KEY, str) else settings.FIREBASE_PRIVATE_KEY,
            "client_email": settings.FIREBASE_CLIENT_EMAIL,
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        })
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin initialized successfully")
    else:
        print("⚠️  Firebase credentials not configured - authentication disabled")
except Exception as e:
    print(f"❌ Firebase Admin initialization error: {e}")


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Firebase token and return user"""
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication: {str(e)}")


async def get_current_user(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get or create user from Firebase token"""
    firebase_uid = token_data["uid"]
    email = token_data.get("email")
    
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if not user:
        user = User(firebase_uid=firebase_uid, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


@router.post("/verify")
async def verify_auth(token_data: dict = Depends(verify_token)):
    """Verify Firebase token"""
    return {"valid": True, "uid": token_data["uid"]}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "firebase_uid": current_user.firebase_uid,
    }

