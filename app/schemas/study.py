from pydantic import BaseModel
from typing import Optional

class StudyMaterialCreate(BaseModel):
    title: str
    description: Optional[str] = None
    subject: str

class StudyMaterialResponse(StudyMaterialCreate):
    id: str
    user_id: str