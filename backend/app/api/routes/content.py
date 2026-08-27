import re

from fastapi import APIRouter

from app.models.schemas import EducationItem, PublicDatasetRow
from app.services.store import store

router = APIRouter(tags=["public-content"])


def anonymize_report(content: str) -> str:
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", content)
    text = re.sub(r"(?<!\w)@\w+", "[AKUN]", text)
    text = re.sub(r"(?:https?://|www\.)\S+", "[TAUTAN]", text, flags=re.I)
    text = re.sub(r"(?<!\d)(?:\+?62|0)[\s-]?\d(?:[\s-]?\d){7,12}(?!\d)", "[NOMOR_TELEPON]", text)
    text = re.sub(r"(?<!\d)\d{8,20}(?!\d)", "[NOMOR_SENSITIF]", text)
    text = re.sub(r"(?i)\b(?:alamat|nama lengkap)\s*[:=-]\s*[^,.\n]+", lambda m: m.group(0).split(":")[0].split("=")[0] + ": [DIHAPUS]", text)
    return text.strip()


@router.get("/education", response_model=list[EducationItem])
def education() -> list[EducationItem]:
    return [EducationItem(**item) for item in store.education()]


@router.get("/dataset", response_model=list[PublicDatasetRow])
def dataset() -> list[PublicDatasetRow]:
    return [PublicDatasetRow(**item) for item in store.public_dataset()]

