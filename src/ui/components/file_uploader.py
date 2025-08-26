import tempfile
from pathlib import Path

import streamlit as st

from src.document_preprocessor import DocumentPreprocessor
from src.retriever import RetrieverConfig, RetrieverFactory
from src.ui.enums import SessionKey
from src.vector_store import VectorStore


class FileUploader:
    """
    파일을 받아서 Vector DB 와 Retriever 초기화 하는 클래스
    현재는 파일 형식은 pdf 만 가능
    """

    def __init__(self):
        self.available_types = ["pdf"]

    def render(self) -> bool:
        st.subheader("자료")
        if uploaded_file := st.file_uploader(
            f"{self.available_types} 형식인 파일을 선택해주세요.",
            type=self.available_types,
        ):
            with st.spinner("문서를 처리중입니다."):
                # 임시 파일 저장 (tempfile 사용)
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=f"_{uploaded_file.name}", prefix="uploaded_"
                ) as temp_file:
                    temp_file.write(uploaded_file.getbuffer())
                    file_path = Path(temp_file.name)

                try:
                    # 2. 문서 전처리
                    preprocessor = DocumentPreprocessor(file_path)
                    documents = preprocessor.process()
                    st.info("문서 전처리 완료")

                    # 3. 벡터 스토어에 저장
                    vector_store = VectorStore()
                    vector_store.add_documents(documents)
                    st.session_state[SessionKey.VECTOR_STORE] = vector_store
                    st.info("VectorStore 초기화 완료")

                    # 4. Retriever 생성
                    config = RetrieverConfig(retriever_type="simple")
                    retriever = RetrieverFactory.create_simple_retriever(vector_store, config)
                    st.session_state[SessionKey.RETRIEVER] = retriever
                    st.info("Retriever 초기화 완료")

                finally:
                    # 파일 삭제 (try-finally로 확실한 정리)
                    if file_path.exists():
                        file_path.unlink()

            if st.button("다음"):
                return True
        return False
