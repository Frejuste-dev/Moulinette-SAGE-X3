from pydantic import BaseModel, ConfigDict
from datetime import datetime

class FileMetadata(BaseModel):
    id: int
    session_id: int
    file_name: str
    file_type: str # "mask", "template", "final"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FileDownload(BaseModel):
    file_name: str
    content_type: str
    # Le contenu binaire sera envoyé via StreamingResponse dans FastAPI, 
    # pas directement via un schéma Pydantic.