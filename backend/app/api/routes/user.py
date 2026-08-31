import os
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.routes.auth import bearer_user
from app.models.schemas import HistorySaveRequest, HistoryUpdateRequest, PasswordChangeRequest, PrivacyUpdateRequest
from app.services.store import store, user_domain

router=APIRouter(prefix="/user",tags=["user"])

def current(authorization:str|None):
    user=bearer_user(authorization)
    if user["role"]!="user": raise HTTPException(403,"Area ini hanya untuk pengguna biasa.")
    return user

def missing(): raise HTTPException(404,"Data tidak ditemukan atau Anda tidak memiliki akses.")

@router.get("/dashboard")
def dashboard(authorization:str|None=Header(default=None)): return user_domain.dashboard(current(authorization)["id"])

@router.get("/histories")
def histories(q:str="",category:str|None=None,risk:str|None=None,favorite:bool|None=None,authorization:str|None=Header(default=None)):
    return user_domain.histories(current(authorization)["id"],q,category,risk,favorite)

@router.post("/histories",status_code=201)
def save_history(payload:HistorySaveRequest,authorization:str|None=Header(default=None)):
    try:return user_domain.save_history(current(authorization)["id"],payload.model_dump())
    except ValueError as exc:raise HTTPException(409,str(exc)) from exc

@router.get("/histories/export")
def export_histories(authorization:str|None=Header(default=None)): return {"histories":user_domain.export(current(authorization)["id"])["histories"]}

@router.get("/histories/{history_id}")
def history(history_id:str,authorization:str|None=Header(default=None)):
    row=user_domain.history_detail(current(authorization)["id"],history_id)
    return row if row else missing()

@router.patch("/histories/{history_id}")
def update_history(history_id:str,payload:HistoryUpdateRequest,authorization:str|None=Header(default=None)):
    row=user_domain.update_history(current(authorization)["id"],history_id,payload.model_dump(exclude_unset=True))
    return row if row else missing()

@router.delete("/histories/{history_id}",status_code=204)
def delete_history(history_id:str,authorization:str|None=Header(default=None)):
    if not user_domain.delete_history(current(authorization)["id"],history_id):missing()

@router.delete("/histories",status_code=200)
def delete_all(authorization:str|None=Header(default=None)):return {"deleted":user_domain.delete_all(current(authorization)["id"])}

@router.get("/reports")
def reports(authorization:str|None=Header(default=None)):return user_domain.reports(current(authorization)["id"])

@router.get("/reports/{report_id}")
def report(report_id:str,authorization:str|None=Header(default=None)):
    row=user_domain.report_detail(current(authorization)["id"],report_id)
    return row if row else missing()

@router.get("/saved-guides")
def guides(authorization:str|None=Header(default=None)):return user_domain.saved_guides(current(authorization)["id"])

@router.post("/saved-guides/{guide_id}",status_code=204)
def save_guide(guide_id:str,authorization:str|None=Header(default=None)):user_domain.save_guide(current(authorization)["id"],guide_id)

@router.delete("/saved-guides/{guide_id}",status_code=204)
def remove_guide(guide_id:str,authorization:str|None=Header(default=None)):
    if not user_domain.remove_guide(current(authorization)["id"],guide_id):missing()

@router.get("/privacy")
def privacy(authorization:str|None=Header(default=None)):return user_domain.privacy(current(authorization)["id"])

@router.put("/privacy")
def update_privacy(payload:PrivacyUpdateRequest,authorization:str|None=Header(default=None)):return user_domain.update_privacy(current(authorization)["id"],payload.model_dump())

class ProfileUpdate(BaseModel): name:str=Field(min_length=2,max_length=80)
@router.patch("/profile")
def profile(payload:ProfileUpdate,authorization:str|None=Header(default=None)):
    user=current(authorization);return store.update_user(user["id"],None,None,name=payload.name)

@router.post("/password")
def password(payload:PasswordChangeRequest,authorization:str|None=Header(default=None)):
    if not store.change_password(current(authorization)["id"],payload.current_password,payload.new_password):raise HTTPException(422,"Kata sandi saat ini tidak sesuai.")
    return {"message":"Kata sandi berhasil diubah."}

@router.get("/data-export")
def data_export(authorization:str|None=Header(default=None)):return user_domain.export(current(authorization)["id"])

class ResetRequest(BaseModel):email:str
class ResetConfirm(BaseModel):token:str;password:str=Field(min_length=8);revoke_sessions:bool=True

@router.post("/password-reset/request")
def request_reset(payload:ResetRequest):
    token=user_domain.request_reset(payload.email)
    response={"message":"Jika email terdaftar, petunjuk reset akan dikirim."}
    if token and os.getenv("EXPOSE_RESET_TOKEN","false").lower()=="true":response["development_token"]=token
    return response

@router.post("/password-reset/confirm")
def confirm_reset(payload:ResetConfirm):
    if not user_domain.reset_password(payload.token,payload.password,payload.revoke_sessions):raise HTTPException(422,"Tautan reset tidak valid atau kedaluwarsa.")
    return {"message":"Kata sandi berhasil diperbarui."}
