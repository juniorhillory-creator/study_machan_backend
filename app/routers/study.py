from fastapi import APIRouter, Depends, HTTPException, status
from app.database import supabase
from app.dependencies import get_current_user
from app.schemas.study import StudyMaterialCreate

router = APIRouter(prefix="/study", tags=["Study Materials"])

@router.post("/materials")
def create_material(payload: StudyMaterialCreate, user=Depends(get_current_user)):
    try:
        data = {
            "title": payload.title,
            "description": payload.description,
            "subject": payload.subject,
            "user_id": user.id
        }
        res = supabase.table("study_materials").insert(data).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/materials")
def get_materials(user=Depends(get_current_user)):
    try:
        res = supabase.table("study_materials").select("*").eq("user_id", user.id).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))