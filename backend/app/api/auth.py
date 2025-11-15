from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from app.database import get_db
from app.models.user import User
from sqlalchemy.orm import Session
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

# Initialize Supabase JWT verification using JWKS
jwks_client = None
supabase_url = None
try:
    if settings.SUPABASE_URL:
        supabase_url = settings.SUPABASE_URL
        # Supabase uses JWKS for JWT verification (RS256)
        jwks_url = f"{supabase_url}/.well-known/jwks.json"
        jwks_client = PyJWKClient(jwks_url)
        print("✅ Supabase JWT verification configured")
    else:
        print("⚠️  Supabase URL not configured - authentication disabled")
except Exception as e:
    print(f"❌ Supabase initialization error: {e}")
    jwks_client = None


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Supabase JWT token and return decoded claims"""
    if not jwks_client:
        raise HTTPException(status_code=401, detail="Authentication not configured")
    
    try:
        token = credentials.credentials
        
        # Get the signing key from JWKS
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Verify JWT using the signing key
        # Supabase JWTs use RS256 algorithm
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="authenticated",
            options={"verify_exp": True}
        )
        
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")


async def get_current_user(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get or create user from Supabase token"""
    supabase_uid = token_data.get("sub")  # Supabase uses 'sub' for user ID
    email = token_data.get("email")
    
    if not supabase_uid:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
    
    user = db.query(User).filter(User.supabase_uid == supabase_uid).first()
    
    if not user:
        user = User(supabase_uid=supabase_uid, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user


@router.post("/verify")
async def verify_auth(token_data: dict = Depends(verify_token)):
    """Verify Supabase token"""
    return {"valid": True, "uid": token_data.get("sub")}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "supabase_uid": current_user.supabase_uid,
    }

