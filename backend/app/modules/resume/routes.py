import os

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from fpdf import FPDF
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.models import User, UserAwardRecord

router = APIRouter(prefix="/resume", tags=["resume"])

UNICODE_FONT_PATHS = [
    "/usr/share/fonts/adobe-source-han-sans/SourceHanSansCN-Regular.otf",
    "/usr/share/fonts/noto/NotoSansCJK-Regular.ttc",
]


def _configure_pdf_font(pdf: FPDF) -> bool:
    for font_path in UNICODE_FONT_PATHS:
        if os.path.exists(font_path):
            pdf.add_font("AppUnicode", fname=font_path)
            pdf.set_font("AppUnicode", size=12)
            return True
    pdf.set_font("Helvetica", size=12)
    return False


def _safe_text(text: str, unicode_ready: bool) -> str:
    if unicode_ready:
        return text
    return text.encode("latin-1", errors="replace").decode("latin-1")


class AwardRecordCreate(BaseModel):
    competition_name: str
    award_name: str
    year: int


class AwardRecordOut(BaseModel):
    id: int
    competition_name: str
    award_name: str
    year: int


@router.post("/records", response_model=AwardRecordOut)
def create_award_record(
    payload: AwardRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AwardRecordOut:
    record = UserAwardRecord(
        user_id=current_user.id,
        competition_name=payload.competition_name.strip(),
        award_name=payload.award_name.strip(),
        year=payload.year,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return AwardRecordOut(
        id=record.id,
        competition_name=record.competition_name,
        award_name=record.award_name,
        year=record.year,
    )


@router.get("/records", response_model=list[AwardRecordOut])
def list_award_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AwardRecordOut]:
    records = (
        db.query(UserAwardRecord)
        .filter(UserAwardRecord.user_id == current_user.id)
        .order_by(UserAwardRecord.year.desc(), UserAwardRecord.id.desc())
        .all()
    )
    return [
        AwardRecordOut(
            id=item.id,
            competition_name=item.competition_name,
            award_name=item.award_name,
            year=item.year,
        )
        for item in records
    ]


@router.get("/pdf")
def export_resume_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    records = (
        db.query(UserAwardRecord)
        .filter(UserAwardRecord.user_id == current_user.id)
        .order_by(UserAwardRecord.year.desc(), UserAwardRecord.id.desc())
        .all()
    )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    unicode_ready = _configure_pdf_font(pdf)

    pdf.set_font_size(16)
    pdf.cell(0, 10, _safe_text("Competition Resume", unicode_ready), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font_size(12)
    pdf.cell(
        0,
        8,
        _safe_text(f"User: {current_user.username}", unicode_ready),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

    if not records:
        pdf.cell(0, 8, _safe_text("No records yet.", unicode_ready), new_x="LMARGIN", new_y="NEXT")
    else:
        for index, record in enumerate(records, start=1):
            line = f"{index}. {record.year} - {record.competition_name} - {record.award_name}"
            pdf.multi_cell(0, 8, _safe_text(line, unicode_ready))

    pdf_bytes = bytes(pdf.output())
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="competition_resume.pdf"',
        },
    )
