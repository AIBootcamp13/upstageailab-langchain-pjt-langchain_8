# **🔧 설정 및 커스터마이징**

이 문서는 configs/config.yaml과 prompts/prompts.yaml 파일을 수정하여 프로젝트의 동작을 사용자의 필요에 맞게 변경하는 방법을 설명합니다.

## **1. 핵심 동작 설정 (configs/config.yaml)**

이 파일은 모델, 데이터 처리 방식 등 애플리케이션의 핵심 동작을 제어합니다.

### **1.1 환경 프로필 전환**

본 프로젝트는 하드웨어 환경에 따라 다른 설정을 사용할 수 있는 **프로필 시스템**을 제공합니다. ENV_PROFILE 환경 변수를 설정하여 프로필을 선택할 수 있습니다.

* **default_cpu**: 고성능 GPU가 없는 환경을 위한 기본 프로필입니다. OpenAI와 같은 외부 API 기반 모델을 사용합니다.  
* **high_gpu**: 로컬 GPU 환경을 위한 프로필입니다. Ollama나 HuggingFace를 통해 로컬에서 모델을 실행할 때 사용합니다.

**프로필 변경 방법 (터미널):**

# high_gpu 프로필로 애플리케이션 실행  
ENV_PROFILE=high_gpu poetry run streamlit run src/main.py

### **1.2 모델 변경**

profiles 섹션에서 사용할 LLM과 임베딩 모델을 변경할 수 있습니다.

```yaml
# configs/config.yaml

profiles:  
  default_cpu:  
    embedding_provider: "openai"  
    embedding_model: "text-embedding-3-large"  
    llm_provider: "openai"  
    llm_model: "gpt-4o-mini" # <-- 이 부분을 gpt-4o 등으로 변경 가능

  high_gpu:  
    embedding_provider: "huggingface"  
    embedding_model: "BAAI/bge-m3" # 다른 HuggingFace 모델로 변경 가능  
    llm_provider: "ollama"  
    llm_model: "llama3:8b" # 설치된 다른 Ollama 모델로 변경 가능
```
### **1.3 데이터 처리 방식 변경**

ingestion 섹션에서 PDF 파서와 텍스트 분할 방식을 제어할 수 있습니다.

```yaml
# configs/config.yaml

ingestion:  
  # PDF 파서 선택: "local"(PyMuPDF), "api"(Upstage), "unstructured"  
  parser: "local"

  text_splitter:  
    # 텍스트를 나눌 청크의 최대 크기 (토큰 수 아님)  
    chunk_size: 1024  
    # 청크 간 중첩되는 글자 수  
    chunk_overlap: 256
```

* **parser**: 문서 처리 성능이나 정확도에 따라 파서를 변경할 수 있습니다. 예를 들어, 복잡한 표나 이미지가 포함된 PDF는 "unstructured"가 더 나은 결과를 보일 수 있습니다.  
* **chunk_size / chunk_overlap**: 이 값을 조정하면 RAG의 검색 정확도와 컨텍스트의 양에 영향을 미칩니다. 문서의 종류에 따라 최적의 값을 찾아 조정할 수 있습니다.

## **2. AI 에이전트 프롬프트 커스터마이징 (prompts/prompts.yaml)**

이 파일은 AI 에이전트의 정체성, 말투, 작업 방식을 결정하는 지시문(프롬프트)을 관리합니다.

### **2.1 초기 초안 생성 프롬프트 (draft_prompt)**

이 프롬프트는 업로드된 PDF를 기반으로 첫 번째 블로그 초안을 생성할 때 사용됩니다.

**기본 프롬프트:**

```yaml
# prompts/prompts.yaml

draft_prompt: |  
  [Identity]  
  당신은 전문 블로그 작가입니다.  
  제공된 자료를 바탕으로 고품질의 블로그 포스트를 작성합니다.

  [Source Material]  
  {content}

  [Instructions]  
  1. 자료의 핵심 내용을 파악하여 적절한 제목을 만드세요.  
  ...
```

**커스터마이징 예시 (학습 노트 스타일로 변경):**

```yaml
# prompts/prompts.yaml

draft_prompt: |  
  [Identity]  
  당신은 지식을 효과적으로 정리하는 튜터입니다.  
  주어진 학습 자료를 학생들이 이해하기 쉬운 블로그 형식의 학습 노트로 만들어주세요.

  [Source Material]  
  {content}

  [Instructions]  
  1. 가장 핵심적인 주제로 제목을 정해주세요.  
  2. 서론, 본론, 결론 구조로 명확하게 내용을 구성해주세요.  
  3. 어려운 용어는 쉽게 풀어서 설명하고, 예시를 포함해주세요.  
  4. 마지막에는 핵심 내용을 요약하는 섹션을 반드시 추가해주세요.
```

### **2.2 대화형 수정 프롬프트 (update_prompt)**

이 프롬프트는 사용자와의 대화를 통해 콘텐츠를 수정하는 Tool-Calling 에이전트의 시스템 프롬프트입니다. 에이전트의 역할과 응답 형식을 정의합니다.

**기본 프롬프트:**

```yaml
# prompts/prompts.yaml

update_prompt: |  
  당신은 사용자의 요청에 따라 블로그 초안을 수정하는 AI 어시스턴트입니다.  
  ...  
  사용자의 요청을 분석하여 다음 두 가지 작업 중 하나를 선택해야 합니다.

  1. **채팅 응답 (type: "chat")**: 단순한 질문에 답하거나, 요청을 수행할 수 없을 때 사용합니다.  
  2. **초안 수정 (type: "draft")**: 사용자의 요청을 반영하여 블로그 초안 전체를 수정할 때 사용합니다.  
  ...
```

이 프롬프트를 수정하여 에이전트의 응답 톤을 바꾸거나, 특정 규칙(예: "항상 존댓말 사용")을 추가할 수 있습니다. 하지만 JSON 응답 형식과 관련된 지시문은 UI와 직접적으로 연결되어 있으므로, 구조를 변경할 때는 주의가 필요합니다.
