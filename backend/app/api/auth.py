from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db
from app.models.user import User
from sqlalchemy.orm import Session
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

print("🧪 TESTING MODE: Authentication validation DISABLED")


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """TESTING MODE: Skip token verification, return mock data"""
    return {
        "sub": "mock-user-123",
        "email": "dev@example.com",
        "aud": "authenticated"
    }


async def get_current_user(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """TESTING MODE: Return mock user without validation"""
    print(f"\n🔐 AUTH - get_current_user called")
    print(f"   Token data: {token_data}")

    try:
        # Try to get or create the mock user (matches brand owner)
        print(f"   🔍 Looking for user with supabase_uid='mock-user-123'")
        user = db.query(User).filter(User.supabase_uid == "mock-user-123").first()

        if not user:
            print(f"   ℹ️  Mock user not found, creating new one...")
            user = User(supabase_uid="mock-user-123", email="dev@example.com")
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"   ✅ Created mock user: ID={user.id}, Email={user.email}")
        else:
            print(f"   ✅ Found existing mock user: ID={user.id}, Email={user.email}")

        return user
    except Exception as e:
        print(f"   ❌ ERROR in get_current_user: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        # Return a mock user if DB fails
        print(f"   ⚠️  Returning fallback MockUser object")
        class MockUser:
            id = "00000000-0000-0000-0000-000000000099"
            email = "dev@example.com"
            supabase_uid = "mock-user-123"
        return MockUser()


@router.post("/verify")
async def verify_auth(token_data: dict = Depends(verify_token)):
    """Verify token (testing mode)"""
    return {"valid": True, "uid": token_data.get("sub")}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user (testing mode)"""
    return {
        "id": str(getattr(current_user, 'id', '00000000-0000-0000-0000-000000000099')),
        "email": getattr(current_user, 'email', 'test@zapcut.video'),
        "supabase_uid": getattr(current_user, 'supabase_uid', 'test-user-123'),
    }
