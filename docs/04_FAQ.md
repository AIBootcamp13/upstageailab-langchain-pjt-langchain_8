# 06_FAQ.md: 자주 하는 질문

**최종 업데이트:** 2025년 8월 26일

---

### **Q1. `SQLite`가 프로젝트 의존성(dependency)으로 포함된 이유가 무엇인가요? `Chroma DB` 때문에 필요한 건가요?**

네, 맞습니다. 로컬 환경에서 **`Chroma DB`를 사용할 때 `SQLite`는 핵심 의존성**입니다.

`Chroma DB`는 벡터(vector) 데이터베이스이지만, 벡터와 관련된 메타데이터(예: 원본 텍스트, 문서 ID, 파일명 등)를 저장하고 관리하기 위해 내부적으로 `SQLite`를 사용합니다. 즉, `Chroma DB`가 벡터 검색을 효율적으로 수행하면서 관련 정보를 함께 조회할 수 있도록 `SQLite`가 데이터베이스 역할을 하는 것입니다.

또한, RAG 프로젝트에서 흔히 사용되는 다른 라이브러리들도 다음과 같은 이유로 `SQLite`를 활용하는 경우가 많습니다.

* **`LangChain`의 캐시 (Cache):** `LangChain`은 반복적인 LLM 호출 비용과 시간을 줄이기 위해 `SQLiteCache` 기능을 제공합니다. 이 기능을 사용하면 이전에 요청했던 질문과 답변을 로컬 `SQLite` 데이터베이스에 저장해두고 재사용할 수 있습니다.
* **`LangGraph`의 체크포인트 (Checkpoint):** 복잡한 에이전트(agent)의 실행 상태를 저장하고 복원하기 위해 `SqliteSaver`를 사용할 수 있습니다. 이를 통해 작업이 중단되더라도 이전 상태에서 안전하게 작업을 재시작할 수 있습니다.

### **Q2. `SQLite`는 오래된 운영체제(OS) 버전 때문에 필요한 의존성인가요?**

아니요, 그렇지 않습니다. **`SQLite`의 사용은 운영체제(OS)의 버전과 전혀 관련이 없습니다.**

`SQLite`를 사용하는 것은 `Chroma DB`나 `LangChain` 같은 최신 라이브러리 개발자들이 의도적으로 선택한 설계입니다. 그 이유는 다음과 같습니다.

* **서버리스(Serverless) 및 이식성(Portable):** `SQLite`는 별도의 서버를 설치하거나 관리할 필요 없이, 단일 파일 형태로 데이터베이스를 운영할 수 있습니다. 이 덕분에 애플리케이션에 내장(embed)하기 쉽고 여러 환경으로 이동하기가 매우 편리합니다.
* **경량성 및 효율성:** 매우 가볍고 빠르며 안정적이어서, 로컬 환경에서 데이터를 저장해야 하는 최신 애플리케이션에 이상적인 선택입니다.
* **Python 표준 라이브러리:** `SQLite`는 `sqlite3`라는 이름으로 Python에 기본적으로 내장되어 있습니다. 따라서 Python 개발자들은 별도의 외부 라이브러리를 추가 설치할 필요 없이 간편하게 로컬 데이터베이스 기능을 구현할 수 있습니다.

----

Task Assessment and Project Analysis
This document provides a comprehensive assessment of the requested tasks, including centralizing configurations, implementing a Streamlit UI, and clarifying the role of the unstructured.io dependency.

1. Centralize Configurations & Remove Hardcoding
The project has a solid configuration foundation using .env and configs/config.yaml, but several components contain hardcoded settings that should be centralized.

Assessment: HIGHLY RECOMMENDED. Centralizing configuration is crucial for maintainability, consistency, and ease of experimentation.

Actionable Items:

Standardize Model and Path Configuration:

The src/generation.py script currently hardcodes LLM_MODEL, EMBEDDING_MODEL_NAME, and VECTOR_STORE_PATH. These should be removed and replaced with the variables already being loaded into src/config.py.

There is an inconsistency between the vector store name in configs/config.yaml (chroma_db_blog_posts) and the path in src/generation.py (chroma_db). This should be unified to use the value from config.yaml via the PERSIST_DIRECTORY variable in src/config.py.

Centralize Hyperparameters:

Chunking: The chunk_size (1000) and chunk_overlap (200) in src/ingestion.py are hardcoded. These values, also mentioned in the data context document , should be moved into configs/config.yaml to allow for easier tuning.

Retrieval: The number of documents to retrieve (k=5 for local search and k=3 for web search) in src/generation.py is hardcoded. These should be externalized to configs/config.yaml.

Standardize Prompts:

The src/generation.py script loads a prompt from prompts/blog_prompts.yaml but then defines a different, more detailed prompt template in the code. The logic should be consolidated to exclusively use the prompts defined in the .yaml file to keep prompts separate from application logic.

2. Implement Streamlit UI Framework
The project is structured to accommodate a UI, with a dedicated src/ui/ directory and modular logic in the BlogGenerator class.

Assessment: FEASIBLE & PLANNED. The 03_CONTEXT_LOG.md explicitly lists a Streamlit UI as a future enhancement. The existing BlogGenerator class can be easily imported and used within a Streamlit application.

Implementation Plan:

Create UI Script: Develop a new script, such as src/ui/app.py.

Import Core Logic: Import the BlogGenerator class from src/generation.py.

Develop Interface:

Use st.title and st.text_input for the user to enter a blog topic.

A st.button will trigger the generation process.

Use st.spinner to indicate that the blog post is being generated.

The main content area will use st.markdown to render the generated blog post in real-time.

Implement Editing/Q&A:

To allow for live modification, add a st.text_area where the user can provide editing instructions (e.g., "Make the tone more casual," "Expand on the section about RAG").

Create a new chain or function that takes the original blog post and the new instruction as context. The blog_editor_prompt from prompts/blog_prompts.yaml is perfectly suited for this task.

Add Entrypoint: Update the README.md with instructions on how to run the application using streamlit run src/ui/app.py.

3. Role of unstructured.io in the Project
Clarification: The unstructured[pptx] dependency is included in pyproject.toml to support the project's goal of creating a "'PPT-to-Blog' Agent," as outlined in the project's context log. While the current data ingestion logic in src/ingestion.py specifically uses PyPDFLoader to process PDF files , the unstructured library is intended for parsing .pptx files in a future phase.

OCR Capabilities:

Yes, unstructured.io is capable of performing Optical Character Recognition (OCR). Its primary function is to extract text from various document formats (like PDF, PPTX, DOCX, etc.). When it encounters a document that is image-based (e.g., a scanned PDF) or contains embedded images with text, it can use an underlying OCR engine (like Tesseract) to extract that text.

Current Usage: In this project, the implemented PyPDFLoader in src/ingestion.py extracts text directly from the text layer of a PDF. It does not use OCR.

Potential Usage: If the project were to process scanned PDFs or .pptx files containing images of text, a different loader (like UnstructuredPDFLoader or UnstructuredPowerPointLoader) would be needed. This would make the unstructured library's OCR capabilities highly valuable. The quality of the extracted text would then depend on the resolution of the images and the accuracy of the configured OCR engine. At present, this feature is not being explicitly used, but the dependency is included for future functionality.