from typing import Any

from PIL.Image import Image
from pydantic import BaseModel, ConfigDict, Field
from streamlit.runtime.uploaded_file_manager import UploadedFile

from ask_your_neighbour.document_store import DocumentStore


class ConversationState(BaseModel):
    files: list[UploadedFile] = Field(default_factory=list)
    all_messages: list[Any] = Field(default_factory=list)
    document_store: DocumentStore = Field(default=DocumentStore())
    image: Image | None = Field(default=None)

    # allow for arbitrary attributes
    model_config = ConfigDict(arbitrary_types_allowed=True)
