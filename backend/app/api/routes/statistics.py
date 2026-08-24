from fastapi import APIRouter
from app.models.schemas import CategoryInfo, KategoriNusaGuard, StatsResponse
from app.services.store import store

router = APIRouter(tags=["public"])
CATEGORIES = [
    CategoryInfo(slug="phishing", name=KategoriNusaGuard.PHISHING, description="Tautan atau situs palsu untuk mencuri data.", examples=["Akun diblokir, klik tautan ini"], prevention=["Periksa domain", "Buka aplikasi resmi secara mandiri"]),
    CategoryInfo(slug="social-engineering", name=KategoriNusaGuard.SOCIAL_ENGINEERING, description="Manipulasi psikologis untuk memperoleh data atau uang.", examples=["Petugas meminta OTP"], prevention=["OTP dan PIN tidak pernah boleh dibagikan", "Hubungi kanal resmi"]),
    CategoryInfo(slug="investment", name=KategoriNusaGuard.PENIPUAN_INVESTASI, description="Janji keuntungan tinggi atau pasti.", examples=["Profit 30% tanpa risiko"], prevention=["Cek izin OJK", "Hindari transfer karena tekanan waktu"]),
    CategoryInfo(slug="recruitment", name=KategoriNusaGuard.PENIPUAN_REKRUTMEN, description="Lowongan palsu yang meminta biaya atau data sensitif.", examples=["Bayar administrasi sebelum interview"], prevention=["Periksa situs perusahaan", "Jangan bayar proses rekrutmen"]),
    CategoryInfo(slug="romance", name=KategoriNusaGuard.PENIPUAN_ROMANSA, description="Membangun kedekatan lalu meminta uang.", examples=["Pasangan daring mendadak butuh transfer"], prevention=["Jangan transfer ke orang yang belum diverifikasi", "Diskusikan dengan orang tepercaya"]),
]

@router.get("/categories", response_model=list[CategoryInfo])
def categories() -> list[CategoryInfo]:
    return CATEGORIES

@router.get("/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    total, counts = store.stats()
    return StatsResponse(total_analyzed=total, category_counts=counts)
