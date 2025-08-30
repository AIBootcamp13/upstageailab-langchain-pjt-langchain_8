# src/ui/components/file_uploader.py
import tempfile
from pathlib import Path

import streamlit as st

from src.config import INGESTION_PARSER
from src.document_preprocessor import DocumentPreprocessor
from src.retriever import RetrieverFactory
from src.ui.enums import SessionKey
from src.vector_store import VectorStore


class FileUploader:
    """
    Handles file uploads and initializes the Vector DB and Retriever.
    """

    def __init__(self):
        self.available_types = ["pdf"]

    def render(self) -> bool:
        """Renders the Streamlit UI for file uploading and processing."""
        st.subheader("자료 업로드")
        if uploaded_file := st.file_uploader(
            f"'{', '.join(self.available_types)}' 형식의 파일을 선택해주세요.",
            type=self.available_types,
        ):
            with st.spinner(f"문서를 처리 중입니다... (파서: '{INGESTION_PARSER}')"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_file.write(uploaded_file.getbuffer())
                    file_path = Path(temp_file.name)

                try:
                    # 1. Preprocess the document
                    preprocessor = DocumentPreprocessor(file_path)
                    documents = preprocessor.process()
                    # *** FIX: Save processed documents to session state for the agent ***
                    st.session_state["processed_documents"] = documents
                    st.info(f"문서 전처리 완료: {len(documents)}개 청크 생성")

                    # 2. Store documents in the vector store
                    vector_store = VectorStore()
                    vector_store.add_documents(documents)
                    st.session_state[SessionKey.VECTOR_STORE] = vector_store
                    st.info("VectorStore 초기화 완료")

                    # 3. Create the retriever
                    retriever = RetrieverFactory.create(vector_store)
                    st.session_state[SessionKey.RETRIEVER] = retriever
                    st.info("Retriever 초기화 완료")

                finally:
                    if file_path.exists():
                        file_path.unlink()

            if st.button("다음 단계로 이동"):
                return True
        return False