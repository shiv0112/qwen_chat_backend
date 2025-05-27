from fastapi import APIRouter, HTTPException
from app.schemas.generate_schema import GenRequest
from app.service.inference import generate_response

router = APIRouter()

@router.post("/generate")
async def generate(req: GenRequest):
    try:
        return await generate_response(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
