import uuid

from openai import OpenAI
from streamlit.runtime.uploaded_file_manager import UploadedFile

from ask_your_neighbour.file_info import FileInfo
from ask_your_neighbour.utils import LOGGER


class DocumentStore:
    files: list[FileInfo]
    vector_store_id: str | None

    def __init__(self):
        self.files = []
        self.vector_store_id = None


    async def upload_files(self, files: list[UploadedFile]) -> None:
        if len(files) == 0:
            return

        client = OpenAI()

        if self.vector_store_id is None:
            self._create_vector_store(client)

        for file in files:
            if file .name in [f.name for f in self.files]:
                continue

            oai_file = client.files.create(
                file=file,
                purpose="user_data"
            )

            # This function uploads a file to the vector store
            client.vector_stores.files.create(
                vector_store_id=self.vector_store_id,
                file_id=oai_file.id,
            )

            self.files.append(
                FileInfo(
                    id=oai_file.id,
                    name=file.name
                )
            )


    def clean_up(self) -> None:
        # This function deletes the vector store and all files in it
        client = OpenAI()

        if self.vector_store_id is not None:
            client.vector_stores.delete(self.vector_store_id)
            self.vector_store_id = None

        for file in self.files:
            client.files.delete(file.id)

        self.files = []


    def _create_vector_store(self, client: OpenAI):
        # This function creates a vector store with the given name.
        vector_store = client.vector_stores.create(
            name=str(uuid.uuid1())
        )

        LOGGER.info(f"Created vector store with id: {vector_store.id}")

        self.vector_store_id = vector_store.id


