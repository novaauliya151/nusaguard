import threading
import time
from collections import defaultdict
from fastapi import APIRouter, Header, HTTPException, Request

from app.models.schemas import AuthResponse, LoginRequest, RegisterRequest, UserPublic
from app.services.admin_domain import canonical_role
from app.services.store import admin_domain, store

router = APIRouter(prefix="/auth", tags=["auth"])

LEGACY_USER_PERMISSIONS = {
    "user": ["analyze", "view_education", "submit_report", "view_own_dashboard"],
    "analyst": ["analyze", "view_education", "submit_report", "view_own_dashboard", "view_aggregate_stats"],
    "moderator": ["analyze", "view_education", "submit_report", "view_own_dashboard", "view_aggregate_stats", "manage_reports"],
    "admin": ["analyze", "view_education", "submit_report", "view_own_dashboard", "view_aggregate_stats", "manage_reports", "manage_users", "view_system_status"],
}


def public_user(user: dict) -> UserPublic:
    role = canonical_role(user["role"])
    permissions = admin_domain.permissions_for(role) or LEGACY_USER_PERMISSIONS.get(role, [])
    legacy = LEGACY_USER_PERMISSIONS.get(user["role"], [])
    return UserPublic(**{**user, "status": user.get("status", "active")}, permissions=sorted(set(permissions + legacy)))


def bearer_user(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sesi pengguna diperlukan.")
    user = store.user_from_token(authorization.removeprefix("Bearer ").strip())
    if not user:
        raise HTTPException(status_code=401, detail="Sesi tidak valid atau sudah kedaluwarsa.")
    return user


def bearer_admin(authorization: str | None) -> dict:
    user = bearer_user(authorization)
    permissions = admin_domain.permissions_for(user["role"])
    if canonical_role(user["role"]) == "user" or not permissions:
        raise HTTPException(status_code=403, detail="Hak akses administrator diperlukan.")
    return user

def bearer_permission(authorization: str | None, permission: str) -> dict:
    user = bearer_admin(authorization)
    if permission not in admin_domain.permissions_for(user["role"]):
        raise HTTPException(status_code=403, detail="Anda tidak memiliki permission untuk tindakan ini.")
    return user

_attempts: dict[str, list[float]] = defaultdict(list)
_attempt_lock = threading.Lock()
MAX_ATTEMPTS, ATTEMPT_WINDOW = 5, 15 * 60

def _login_key(request: Request, email: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{email.casefold()}"


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest) -> AuthResponse:
    if payload.confirm_password is not None and payload.password != payload.confirm_password:
        raise HTTPException(status_code=422, detail="Konfirmasi kata sandi tidak sama.")
    if not payload.accept_terms or not payload.accept_privacy:
        raise HTTPException(status_code=422, detail="Persetujuan syarat dan kebijakan privasi diperlukan.")
    if not any(ch.isalpha() for ch in payload.password) or not any(ch.isdigit() for ch in payload.password):
        raise HTTPException(status_code=422, detail="Kata sandi harus berisi huruf dan angka.")
    user = store.create_user(payload.name, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=409, detail="Email sudah terdaftar.")
    token, authenticated = store.authenticate(payload.email, payload.password)  # type: ignore[misc]
    return AuthResponse(access_token=token, user=public_user(authenticated))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request) -> AuthResponse:
    key, now = _login_key(request, payload.email), time.monotonic()
    with _attempt_lock:
        _attempts[key] = [stamp for stamp in _attempts[key] if now - stamp < ATTEMPT_WINDOW]
        if len(_attempts[key]) >= MAX_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Terlalu banyak percobaan login. Coba lagi beberapa saat.")
    result = store.authenticate(payload.email, payload.password, payload.remember_me)
    if not result:
        with _attempt_lock: _attempts[key].append(now)
        raise HTTPException(status_code=401, detail="Email atau kata sandi salah.")
    with _attempt_lock: _attempts.pop(key, None)
    token, user = result
    store.add_activity(user["email"], "login", "authentication", user["id"], "Login berhasil")
    return AuthResponse(access_token=token, user=public_user(user))


@router.get("/me", response_model=UserPublic)
def me(authorization: str | None = Header(default=None)) -> UserPublic:
    return public_user(bearer_user(authorization))

@router.post("/logout", status_code=204)
def logout(authorization: str | None = Header(default=None)) -> None:
    user = bearer_user(authorization)
    token = authorization.removeprefix("Bearer ").strip() if authorization else ""
    store.revoke_token(token)
    store.add_activity(user["email"], "logout", "authentication", user["id"], "Logout berhasil")

