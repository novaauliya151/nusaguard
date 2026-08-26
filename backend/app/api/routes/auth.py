from fastapi import APIRouter, Header, HTTPException

from app.models.schemas import AuthResponse, LoginRequest, RegisterRequest, UserPublic
from app.services.store import store

router = APIRouter(prefix="/auth", tags=["auth"])

ROLE_PERMISSIONS = {
    "user": ["analyze", "view_education", "submit_report", "view_own_dashboard"],
    "analyst": ["analyze", "view_education", "submit_report", "view_own_dashboard", "view_aggregate_stats"],
    "moderator": ["analyze", "view_education", "submit_report", "view_own_dashboard", "view_aggregate_stats", "manage_reports"],
    "admin": ["analyze", "view_education", "submit_report", "view_own_dashboard", "view_aggregate_stats", "manage_reports", "manage_users", "view_system_status"],
}


def public_user(user: dict) -> UserPublic:
    return UserPublic(**user, permissions=ROLE_PERMISSIONS.get(user["role"], []))


def bearer_user(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sesi pengguna diperlukan.")
    user = store.user_from_token(authorization.removeprefix("Bearer ").strip())
    if not user:
        raise HTTPException(status_code=401, detail="Sesi tidak valid atau sudah kedaluwarsa.")
    return user


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest) -> AuthResponse:
    user = store.create_user(payload.name, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=409, detail="Email sudah terdaftar.")
    token, authenticated = store.authenticate(payload.email, payload.password)  # type: ignore[misc]
    return AuthResponse(access_token=token, user=public_user(authenticated))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    result = store.authenticate(payload.email, payload.password)
    if not result:
        raise HTTPException(status_code=401, detail="Email atau kata sandi salah.")
    token, user = result
    return AuthResponse(access_token=token, user=public_user(user))


@router.get("/me", response_model=UserPublic)
def me(authorization: str | None = Header(default=None)) -> UserPublic:
    return public_user(bearer_user(authorization))

