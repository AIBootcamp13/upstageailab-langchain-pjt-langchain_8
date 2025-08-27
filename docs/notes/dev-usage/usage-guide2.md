# **RAG 블로그 생성기 사용 가이드**

**최종 업데이트:** 2025년 8월 28일

이 문서는 RAG 기반 블로그 포스트 생성기 프로젝트의 설정 및 사용 방법을 안내합니다.

## **📋 사전 준비**

프로젝트를 실행하기 전에 다음 단계를 완료해야 합니다.

### **1. Python 종속성 설치**

프로젝트 루트 디렉토리에서 Poetry를 사용하여 필요한 모든 라이브러리를 설치합니다.

```bash
poetry install
```

### **2. .env 파일 설정**

프로젝트 루트에 .env 파일을 생성하고 필요한 API 키를 추가합니다.

```env
# .env 파일 예시  
OPENAI_API_KEY="sk-..."  
UPSTAGE_API_KEY="up-..."  
TAVILY_API_KEY="tvly-..."
```

### **3. Ollama 로컬 LLM 서버 실행 (선택 사항)**

high_gpu 프로필을 사용하여 로컬 모델을 실행할 경우, 터미널을 열고 Ollama 서버를 활성화합니다.

```bash
ollama run gpt-oss:20b
```

## **🚀 Streamlit 웹 UI 실행 방법**

이 프로젝트는 사용하기 쉬운 웹 인터페이스를 제공합니다. 아래 명령어를 사용하여 Streamlit 앱을 실행하세요.

**명령어:**

```bash
streamlit run src/app.py

poetry run streamlit run src/app.py
```
# Optional: if you already have a script run_streamlit.sh and want to run it through Poetry:
```bash
poetry run bash scripts/run_streamlit.sh
```

실행 후, 웹 브라우저에서 제공된 URL(보통 http://localhost:8501)에 접속하면 GitHub 인증부터 파일 업로드, 블로그 초안 생성 및 수정, 발행까지 모든 과정을 그래픽 인터페이스를 통해 진행할 수 있습니다.

## **⌨️ CLI 실행 워크플로우 (대안)**

명령줄 인터페이스를 선호하는 경우, 프로젝트는 **설정 확인 → 인덱싱 → 생성**의 3단계로 실행할 수 있습니다.

### **단계 1: 설정 확인 (선택 사항)**

`src/config.py` 스크립트를 실행하여 .env 파일의 API 키와 디렉토리 경로가 올바르게 로드되었는지 확인할 수 있습니다.

**명령어:**

```bash
python -m src.config
```

### **단계 2: 데이터 인덱싱 (최초 1회)**

`src/indexing.py` 스크립트를 실행하여 `data/` 디렉토리에 있는 PDF 문서를 벡터로 변환하고, 검색 가능한 인덱스를 생성합니다. 이 작업은 PDF 파일이 추가되거나 변경될 때마다 한 번씩 실행하면 됩니다.

**명령어:**

```bash
python -m src.indexing
```

### **단계 3: 블로그 포스트 생성**

`src/main.py` 스크립트를 `--topic` 인자와 함께 실행하여 특정 주제에 대한 블로그 포스트를 생성합니다.

**명령어:**

```bash
python -m src.main --topic "최신 AI 아키텍처에 대한 심층 분석"
```
