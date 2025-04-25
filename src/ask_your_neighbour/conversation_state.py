from typing import Any
from pydantic import BaseModel, Field, ConfigDict
from streamlit.runtime.uploaded_file_manager import UploadedFile

class ConversationState(BaseModel):

    files: list[UploadedFile] = Field(default_factory=list)
    all_messages: list[Any] = Field(default_factory=list)
    
    # allow for arbitrary attributes
    model_config = ConfigDict(arbitrary_types_allowed=True)
