"""Authentication API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from app.database import get_db
from app.models.user import User
from sqlalchemy.orm import Session
from app.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

# Initialize Supabase JWT verification
jwks_client = None
supabase_url = None

if settings.SUPABASE_URL:
    try:
        supabase_url = settings.SUPABASE_URL
        jwks_url = f"{supabase_url}/.well-known/jwks.json"
        jwks_client = PyJWKClient(jwks_url)
        logger.info("Supabase JWT verification configured")
    except Exception as e:
        logger.error(f"Supabase initialization error: {e}")
        jwks_client = None
else:
    logger.warning("SupABASE_URL not configured - authentication disabled")


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Supabase JWT token."""
    if not supabase_url:
        raise HTTPException(status_code=401, detail="Supabase URL not configured")
    
    try:
        token = credentials.credentials
        
        # Decode header to check algorithm
        header = jwt.get_unverified_header(token)
        token_algorithm = header.get("alg")
        
        # Verify based on algorithm
        if token_algorithm == "RS256":
            if not jwks_client:
                raise HTTPException(status_code=401, detail="JWKS client not configured")
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience="authenticated",
                options={"verify_exp": True, "verify_signature": True}
            )
        elif token_algorithm == "HS256":
            if not settings.SUPABASE_JWT_SECRET:
                raise HTTPException(status_code=401, detail="HS256 requires SUPABASE_JWT_SECRET")
            decoded_token = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_exp": True, "verify_signature": True}
            )
        else:
            raise HTTPException(status_code=401, detail=f"Unsupported algorithm: {token_algorithm}")
        
        # Verify issuer
        if "iss" in decoded_token:
            issuer = decoded_token["iss"]
            if "supabase.co" not in issuer and "supabase.io" not in issuer:
                raise HTTPException(status_code=401, detail=f"Invalid issuer: {issuer}")
        
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")


async def get_current_user(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get or create user from token."""
    try:
        supabase_uid = token_data.get("sub")
        email = token_data.get("email")
        
        if not supabase_uid:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        user = db.query(User).filter(User.supabase_uid == supabase_uid).first()
        
        if not user:
            user = User(
                supabase_uid=supabase_uid,
                email=email,
                created_at=datetime.utcnow()
            )
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
                logger.info(f"Created new user: {supabase_uid}")
            except Exception as db_error:
                db.rollback()
                logger.error(f"Database error creating user: {db_error}", exc_info=True)
                raise HTTPException(status_code=500, detail="Failed to create user account")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_current_user error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/verify")
async def verify_auth(token_data: dict = Depends(verify_token)):
    """Verify token endpoint."""
    return {"valid": True, "uid": token_data.get("sub")}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "supabase_uid": current_user.supabase_uid,
    }

