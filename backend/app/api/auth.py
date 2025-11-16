from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
import sys
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
    """Verify Supabase JWT token and return decoded claims
    
    Supports both RS256 (JWKS) and HS256 (JWT secret) algorithms for compatibility.
    Modern Supabase projects use RS256, but legacy projects may use HS256.
    """
    if not supabase_url:
        raise HTTPException(
            status_code=401,
            detail="Supabase URL not configured. Please set SUPABASE_URL environment variable."
        )
    
    try:
        token = credentials.credentials
        
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Decode header to check the algorithm
        try:
            header = jwt.get_unverified_header(token)
            token_algorithm = header.get("alg")
        except jwt.DecodeError:
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        # Verify token based on algorithm
        if token_algorithm == "RS256":
            # Modern Supabase: Use JWKS
            if not jwks_client:
                raise HTTPException(
                    status_code=401,
                    detail="JWKS client not configured. Cannot verify RS256 tokens."
                )
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                decoded_token = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256"],
                    audience="authenticated",
                    options={"verify_exp": True, "verify_signature": True}
                )
            except Exception as e:
                raise HTTPException(
                    status_code=401,
                    detail=f"Failed to verify RS256 token: {str(e)}"
                )
        elif token_algorithm == "HS256":
            # Legacy Supabase: Use JWT secret
            if not settings.SUPABASE_JWT_SECRET:
                raise HTTPException(
                    status_code=401,
                    detail="HS256 tokens require SUPABASE_JWT_SECRET. Please configure it or migrate to RS256."
                )
            try:
                decoded_token = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    audience="authenticated",
                    options={"verify_exp": True, "verify_signature": True}
                )
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token has expired")
            except jwt.InvalidSignatureError:
                raise HTTPException(status_code=401, detail="Invalid token signature")
            except jwt.DecodeError as e:
                raise HTTPException(status_code=401, detail=f"Token decode error: {str(e)}")
            except jwt.InvalidTokenError as e:
                raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
            except Exception as e:
                # Log for debugging
                print(f"❌ HS256 verification error: {type(e).__name__}: {e}", file=sys.stderr)
                raise HTTPException(
                    status_code=401,
                    detail=f"Failed to verify HS256 token: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=401,
                detail=f"Unsupported token algorithm: {token_algorithm}. Expected RS256 or HS256."
            )
        
        # Verify the token is from Supabase (check issuer)
        if "iss" in decoded_token:
            issuer = decoded_token["iss"]
            if "supabase.co" not in issuer and "supabase.io" not in issuer:
                raise HTTPException(
                    status_code=401,
                    detail=f"Invalid token issuer. Expected Supabase issuer but got: {issuer}"
                )
        
        return decoded_token
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Supabase token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")


async def get_current_user(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get or create user from Supabase token"""
    try:
        supabase_uid = token_data.get("sub")  # Supabase uses 'sub' for user ID
        email = token_data.get("email")
        
        if not supabase_uid:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        user = db.query(User).filter(User.supabase_uid == supabase_uid).first()
        
        if not user:
            user = User(supabase_uid=supabase_uid, email=email)
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
            except Exception as db_error:
                db.rollback()
                # Log but don't expose internal errors
                print(f"❌ Database error creating user: {db_error}", file=sys.stderr)
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create user account. Please try again."
                )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        # Catch any other unexpected errors
        print(f"❌ get_current_user error: {type(e).__name__}: {e}", file=sys.stderr)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during authentication"
        )


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

