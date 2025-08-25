# 간단히 LlamaIndex 사용하기 – RAG 기반 문서 검색 & 챗봇 구축

## 서론

최근 AI 개발자들 사이에서 **Retrieval-Augmented Generation (RAG)** 이슈가 뜨거운 화두가 되고 있습니다.  
문서가 많아질수록 단순히 챗봇이 답변만 만들어내는 것이 아니라, 실제 자료를 찾아 **“내가 아는 것”**과 **“내가 찾은 것”**을 결합해 보다 정확한 응답을 제공하는 모델이 필요합니다.  

그런데 RAG를 구현하기 위해선 **벡터 인덱싱** → **리트리버** → **질의 엔진**과 같은 파이프라인을 손수 구성해야 할 수도 있습니다.  
LlamaIndex(이전 이름: GPT Index)는 이러한 과정을 추상화해 주는 파이썬 라이브러리입니다.  

이 글에서는 **LlamaIndex를 한 줄로 설치**하고, **문서 로딩 → 인덱스 생성 → 질의**까지의 흐름을 단계별로 보여드리며, RAG 기반 챗봇을 빠르게 만들 수 있는 방법을 정리합니다.

> **목표**  
> * LlamaIndex의 기본 개념과 설치 방법  
> * 문서(텍스트, PDF 등)를 인덱싱하고 질의하는 기본 예제  
> * VectorStoreIndex, Retriever, RouterQueryEngine을 활용한 RAG 구축  
> * 실제 대화형 챗봇을 만들 때 유용한 팁

---

## 1. LlamaIndex 시작하기

### 1.1 설치

```bash
pip install llama-index
```

> **Tip**: 최신 기능을 활용하려면 `llama-index[all]` 옵션을 사용해 전체 의존성을 설치하세요.

### 1.2 API Key 준비

LlamaIndex는 OpenAI, Gemini, Claude 등 다양한 LLM을 연결합니다.  
예시에서는 OpenAI의 GPT‑3.5/4를 사용합니다.

```python
import os
os.environ["OPENAI_API_KEY"] = "sk-..."   # 자신의 키를 입력하세요
```

---

## 2. 문서 로딩과 노드 파싱

### 2.1 SimpleDirectoryReader

`SimpleDirectoryReader`는 디렉터리 내에 있는 `.txt`, `.md`, `.pdf` 등 파일을 자동으로 읽어줍니다.

```python
from llama_index import SimpleDirectoryReader

documents = SimpleDirectoryReader(input_files=["data/doc1.pdf", "data/doc2.txt"]).load_data()
```

### 2.2 노드 파싱

노드는 LlamaIndex가 인덱스에 저장하는 기본 단위입니다.  
기본 파서(`NodeParser`)는 문장을 분할하거나 문서 단위로 처리합니다.

```python
from llama_index.core.node_parser import SentenceSplitter

node_parser = SentenceSplitter(chunk_size=512)   # 512 토큰 단위로 분할
nodes = node_parser.get_nodes_from_documents(documents)
```

> **주의**: 문서가 너무 크면 `chunk_size`를 조절해 토큰 수를 관리하세요.

---

## 3. 인덱스 생성

### 3.1 VectorStoreIndex

가장 흔히 사용하는 인덱스 타입입니다. FAISS, Milvus, Qdrant 등 백엔드를 지정할 수 있습니다.

```python
from llama_index import VectorStoreIndex

index = VectorStoreIndex.from_documents(documents)
```

### 3.2 인덱스 저장 및 불러오기

```python
index.storage_context.persist("./storage")          # 저장

# 필요할 때 로드
from llama_index import StorageContext, load_index_from_storage

storage_context = StorageContext.from_defaults(persist_dir="./storage")
loaded_index = load_index_from_storage(storage_context)
```

---

## 4. 질의 엔진 만들기

### 4.1 기본 질의

```python
query_engine = index.as_query_engine()
response = query_engine.query("인공지능이란 무엇인가?")
print(response)
```

### 4.2 VectorIndexRetriever 설정

Retriver는 사용자의 질문과 가장 유사한 문서를 찾아 반환합니다.

```python
from llama_index.retrievers import VectorIndexRetriever

retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=5,      # 가장 유사한 5개 문서
)

query_engine = retriever.as_query_engine()
```

### 4.3 RouterQueryEngine (다중 도구)

RAG를 확장해 두 개 이상의 도구(예: 리스트, 벡터)로 분기시키는 예시입니다.

```python
from llama_index.query_engine.router_query_engine import RouterQueryEngine
from llama_index.selectors.pydantic_selectors import PydanticSingleSelector
from llama_index.tools.query_engine import QueryEngineTool

# 리스트 도구: 전체 문서 개요를 제공
list_tool = QueryEngineTool.from_defaults(
    query_engine=index.as_query_engine(),
    description="전체 문서 리스트 제공",
)

# 벡터 도구: 문서 검색 결과 반환
vector_tool = QueryEngineTool.from_defaults(
    query_engine=retriever.as_query_engine(),
    description="특정 문서 내용 검색",
)

router = RouterQueryEngine(
    selector=PydanticSingleSelector.from_defaults(),
    query_engine_tools=[list_tool, vector_tool],
)

print(router.query("2023년 인공지능 트렌드"))
```

> **Tip**: `PydanticSingleSelector`는 가장 유사한 도구를 자동 선택해 줍니다.

---

## 5. RAG 기반 챗봇 만들기

### 5.1 LLM과 연결

```python
from llama_index import OpenAIEmbedding, OpenAI
from llama_index.llms import OpenAIChat

llm = OpenAIChat(model="gpt-4o-mini")   # 작은 모델이면 속도 ↑
```

### 5.2 LlamaIndex와 LLM 결합

```python
from llama_index import LLMPredictor, ServiceContext

llm_predictor = LLMPredictor(llm=llm)
service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)

# 다시 인덱스 생성 (서비스 컨텍스트 연결)
index = VectorStoreIndex.from_documents(documents, service_context=service_context)
```

### 5.3 대화형 챗봇

```python
chat_engine = index.as_chat_engine(
    context_window=4096,
    similarity_top_k=3,
    verbose=True,
)

chat_engine.chat("AI가 어떻게 학습되는지 알려줘.")
```

> **핵심 포인트**  
> * `context_window`는 LLM의 토큰 제한 내에서 질의와 컨텍스트를 관리합니다.  
> * `similarity_top_k`는 검색된 문서 수를 조절해 응답 정확도를 높입니다.

---

## 6. 실전 팁 & 트러블슈팅

| 상황 | 해결책 |
|------|--------|
| **문서 수가 1000개 이상** | `VectorStoreIndex.from_documents(..., max_nodes_per_chunk=128)`으로 메모리 절감 |
| **FAISS가 메모리 초과** | `storage_context`에 `faiss_index_cls="faiss.IndexIVFFlat"` 지정하거나 `vector_store="disk"` 사용 |
| **LLM 응답이 너무 길다** | `response_length=512` 옵션으로 제한 |
| **API 키 누락** | `os.environ["OPENAI_API_KEY"]` 확인, 또는 `llm = OpenAIChat(api_key="sk-...")` 명시 |
| **토큰 초과 오류** | `token_counter`로 문서 토큰 수 확인 후 `chunk_size` 조정 |

---

## 결론

- **LlamaIndex**는 문서 로딩 → 노드 파싱 → 인덱스 생성 → 질의 엔진 구축까지의 과정을 단순화해 줍니다.  
- **VectorStoreIndex**와 **Retriever**, **RouterQueryEngine** 같은 빌트인 도구를 활용하면 RAG 기반 챗봇을 빠르게 구현할 수 있습니다.  
- OpenAI 같은 LLM과 결합해 **대화형 문서 탐색**이 가능하며, 추후에 **멀티모달**이나 **스마트 에이전트** 같은 고급 기능도 쉽게 확장할 수 있습니다.  

RAG를 통해 AI가 *정보를 찾는* 단계와 *생성하는* 단계를 명확히 분리하면, **정확도**와 **투명성**을 동시에 잡을 수 있습니다.  
다음 단계로는 **실시간 데이터 스트리밍**, **사용자 맞춤 인덱스**, **모델 배포**까지 확장해 보세요.

Happy coding! 🚀