from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_upstage.document_parse import UpstageDocumentParseLoader

from src.config import UPSTAGE_API_KEY


class DocumentPreprocessor:
    """
    File IO 를 입력 받아서 langchain 의 Document list 로 만드는 모듈
    document_loader 와 text_splitter 를 사용해서 전처리를 한다.
    """

    def __init__(self, filepath: Path):
        self.loader = UpstageDocumentParseLoader(
            filepath, api_key=UPSTAGE_API_KEY, split="page", output_format="markdown"
        )
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=256)

    def process(self) -> list[Document]:
        documents = self.loader.load()
        return self.splitter.split_documents([self._sanitize_doc(doc) for doc in documents])

    @staticmethod
    def _sanitize_doc(doc: Document) -> Document:
        # UpstageDocumentParseLoader 를 사용할 경우,
        # metadata 에 coordinates 가 들어있어 chromadb 를 만들때 문제가 발생한다.
        # 그래서 그 데이터를 삭제한 primitive type 만 가지는 Document 를 만들어서 반환한다.
        meta = dict(doc.metadata)
        if "coordinates" in meta:
            meta.pop("coordinates")
        return Document(
            page_content=doc.page_content,
            metadata=meta,
        )
