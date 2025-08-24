from llama_index.core import SimpleDirectoryReader


def load_ppt_documents(directory_path):
    """지정된 디렉토리에서 PPT 파일들을 로드합니다."""
    # SimpleDirectoryReader는 내부적으로 unstructured를 사용해
    # .pptx, .pdf, .docx 등 다양한 파일을 자동으로 파싱합니다.
    reader = SimpleDirectoryReader(input_dir=directory_path)
    docs = reader.load_data()
    print(f"총 {len(docs)}개의 문서를 로드했습니다. (PPT 슬라이드별로 분리될 수 있음)")
    return docs


# 'ppt_data' 폴더에 있는 PPT 파일을 로드
documents = load_ppt_documents(
    "/home/wb2x/workspace/upstageailab-langchain-pjt-langchain_8/notebooks/wb2x/Part 2. RAG with LlamaIndex/강의 교안"
)


def main():
    pass


if __name__ == "__main__":
    main()
