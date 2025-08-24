# RAG 블로그 생성기 사용 가이드

이 문서는 RAG 기반 블로그 포스트 생성기 프로젝트의 설정 및 사용 방법을 안내합니다.

## 📋 사전 준비

프로젝트를 실행하기 전에 다음 단계를 완료해야 합니다.

### 1. Python 종속성 설치

프로젝트 루트 디렉토리에서 `Poetry`를 사용하여 필요한 모든 라이브러리를 설치합니다.

```bash
poetry install
```
### **2. .env 파일 설정**

프로젝트 루트에 .env 파일을 생성하고 필요한 API 키를 추가합니다.

# .env 파일 예시
OPENAI_API_KEY="sk-..."
UPSTAGE_API_KEY="up-..."
TAVILY_API_KEY="tvly-..."

### **3. Ollama 로컬 LLM 서버 실행**

터미널을 열고 gpt-oss-20b 모델을 실행하여 로컬 LLM 서버를 활성화합니다.

ollama run gpt-oss-20b

### **4. 소스 PDF 파일 추가**

블로그 포스트의 기반 자료로 사용할 PDF 파일들을 data/source_pdfs/ 디렉토리에 추가합니다.

## **🚀 프로젝트 실행 워크플로우**

프로젝트는 **설정 확인 → 인덱싱 → 생성**의 3단계로 실행됩니다.

### **단계 1: 설정 확인 (선택 사항)**

`src/config.py` 스크립트를 실행하여 .env 파일의 API 키와 디렉토리 경로가 올바르게 로드되었는지 확인할 수 있습니다.

**명령어:**

```bash
python -m src.config
```

**예상 출력:**

```bash
ic| 'Configuration Validation'
ic| ROOT_DIR: /home/wb2x/workspace/upstageailab-langchain-pjt-langchain_8
ic| SOURCE_PDFS_DIR: /home/wb2x/workspace/upstageailab-langchain-pjt-langchain_8/data/source_pdfs
...
```

### **단계 2: 데이터 인덱싱 (최초 1회)**

`src/indexing.py` 스크립트를 실행하여 `data/source_pdfs/`에 있는 모든 PDF 문서를 벡터로 변환하고, `vector_store/` 디렉토리에 검색 가능한 인덱스를 생성합니다. 이 작업은 `PDF` 파일이 추가되거나 변경될 때마다 한 번씩 실행하면 됩니다.

**명령어:**

```bash
python -m src.indexing
```
**예상 출력:**

```bash
INFO: --- 벡터 스토어 생성을 시작합니다 ---
INFO: `data/source_pdfs'에서 ...개의 PDF 파일을 찾았습니다.
...
INFO: --- 벡터 스토어 생성이 완료되었습니다 ---
```

### **단계 3: 블로그 포스트 생성**

`src/main.py` 스크립트를 `--topic` 인자와 함께 실행하여 특정 주제에 대한 블로그 포스트를 생성합니다. 스크립트는 인덱싱된 PDF 데이터와 웹 검색 결과를 종합하여 콘텐츠를 만듭니다.

**명령어:**
```bash
python -m src.main --topic` "최신 AI 아키텍처에 대한 심층 분석"
```
예상 출력:
생성된 블로그 포스트가 터미널에 출력되고, 결과물은 `output/` 디렉토리에 마크다운(.md) 파일로 자동 저장됩니다.

--- 생성된 블로그 포스트 ---

# 최신 AI 아키텍처 심층 분석: 트랜스포머를 넘어서

AI 기술이 빠르게 발전하면서...

---
✅ 블로그 포스트가 성공적으로 저장되었습니다: `output` `최신_ai_아키텍처에_대한_심층_분석.md `
