from pydantic import BaseModel


class FileInfo(BaseModel):
    id: str
    name: str
