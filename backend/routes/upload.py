"""
Cortex — Upload Routes
========================
POST /api/upload/csv — Upload a CSV file for analysis
GET  /api/upload/files — List uploaded files
DELETE /api/upload/files — Clear all uploaded files
"""

import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

router   = APIRouter(prefix="/api/upload", tags=["upload"])
UPLOADS  = Path(__file__).parent.parent.parent / "uploads"
UPLOADS.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".txt"}
MAX_FILE_SIZE_MB   = 10


@router.post("/csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file to be analyzed by the agent.
    The csv_analyzer tool will automatically use the most recently uploaded file.
    """
    # Validate extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Only CSV and TXT files are allowed. Got: {suffix}"
        )

    # Read and check size
    contents = await file.read()
    size_mb  = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Max allowed: {MAX_FILE_SIZE_MB}MB."
        )

    # Save to uploads folder
    save_path = UPLOADS / file.filename
    with open(save_path, "wb") as f:
        f.write(contents)

    return {
        "success":   True,
        "filename":  file.filename,
        "size_mb":   round(size_mb, 3),
        "message":   f"'{file.filename}' uploaded successfully. You can now ask Cortex to analyze it.",
    }


@router.get("/files")
async def list_files():
    """List all uploaded files."""
    files = []
    for f in UPLOADS.iterdir():
        if f.is_file():
            files.append({
                "filename": f.name,
                "size_kb":  round(f.stat().st_size / 1024, 2),
            })
    return {"files": files, "count": len(files)}


@router.delete("/files")
async def clear_files():
    """Delete all uploaded files."""
    deleted = 0
    for f in UPLOADS.iterdir():
        if f.is_file():
            f.unlink()
            deleted += 1
    return {"success": True, "deleted": deleted}