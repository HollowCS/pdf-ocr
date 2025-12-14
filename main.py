from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from services.extract_pdf import extract_pdf
import pprint
import types
app = FastAPI()


@app.post("/extract-pdf-text-only/")
async def extract_pdf_text_only(file: UploadFile = File(...)):
    """
    FastAPI endpoint to extract only text from uploaded PDF

    Args:
        file: Uploaded PDF file

    Returns:
        JSON response with full text only
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        pdf_bytes = await file.read()
        result = extract_pdf_content_from_bytes(pdf_bytes)

        return JSONResponse(content={
            "full_text": result["full_text"],
            "statistics": result["statistics"]
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))