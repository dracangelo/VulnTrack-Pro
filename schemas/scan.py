from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ScanBase(BaseModel):
    target_id: int

class ScanCreate(ScanBase):
    pass

class ScanResponse(BaseModel):
    id: int
    target_id: int
    status: str
    result: Optional[str]
    created_at: datetime
    finished_at: Optional[datetime]

    class Config:
        orm_mode = True
