import os
import shutil
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.services.extraction_service import extract_text, chunk_text
from app.services.db_service import save_document, save_report, get_report, get_all_chunks, get_document
from app.services.semantic_service import index_source_document
from app.services.exact_match_service import build_exact_match_index
from app.services.report_service import generate_report

router = APIRouter()

class CheckTextRequest(BaseModel):
    text: str
    title: Optional[str] = None

def process_text_and_generate_report(
    text: str, 
    filename: str, 
    doc_type: str = "uploaded", 
    user_id: Optional[int] = None
) -> dict:
    """Shared pipeline: chunk_text -> save_document -> index_source_document ->
    build_exact_match_index -> generate_report -> save_report."""
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")
        
    # 1. Chunk text
    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Could not extract text chunks")
        
    # 2. Save document record with specified doc_type and owner user_id
    document_id = save_document(filename, doc_type, user_id=user_id)
    
    # 3. Index its chunks into the semantic database (pgvector)
    index_source_document(document_id, chunks)
    
    # 4. Build the exact-match LSH index from ALL previously stored
    #    source chunks, excluding the document we just processed so it
    #    doesn't match itself.
    existing_chunks = get_all_chunks(exclude_document_id=document_id)
    if existing_chunks:
        lsh, minhashes = build_exact_match_index(existing_chunks, threshold=0.5)
    else:
        lsh = None
        minhashes = None
        
    # 5. Generate the plagiarism report
    report_data = generate_report(chunks, lsh, minhashes, document_id)
    
    # 6. Save the report to the database
    final_report = {"filename": filename, "report": report_data}
    save_report(document_id, final_report)
    
    # 7. Return the report JSON
    return {"document_id": document_id, "filename": filename, "report": report_data}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    # Ensure temp dir exists
    os.makedirs("temp", exist_ok=True)
    temp_path = os.path.join("temp", file.filename)
    
    # Save uploaded file to temp directory
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Extract text from the uploaded file
        text = extract_text(temp_path)
        return process_text_and_generate_report(
            text, 
            file.filename, 
            doc_type="uploaded", 
            user_id=current_user["id"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/check-text")
async def check_text(
    request: CheckTextRequest,
    current_user: dict = Depends(get_current_user)
):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    display_title = request.title.strip() if (request.title and request.title.strip()) else "Pasted Text"
    try:
        return process_text_and_generate_report(
            request.text, 
            display_title, 
            doc_type="pasted", 
            user_id=current_user["id"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{document_id}")
async def get_document_report(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Retrieves a previously saved report via db_service.get_report.
    
    Enforces that the requester is the owner of the document (returns 403 otherwise).
    """
    doc = get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if doc.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this document"
        )
        
    report_data = get_report(document_id)
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")
    return report_data
