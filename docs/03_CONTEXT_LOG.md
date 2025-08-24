# **프로젝트 현황 요약 (2025년 8월 24일 기준)**

## **1. 프로젝트 개요**

* **프로젝트명:** RAG 기반 블로그 포스트 생성기
* **목표:** 사용자가 제공한 PDF 문서와 웹 검색 결과를 결합하는 하이브리드 RAG(Retrieval-Augmented Generation) 파이프라인을 구축하여, 특정 주제에 대한 고품질 기술 블로그 포스트를 자동으로 생성합니다.
* **핵심 기술:** LangChain, ChromaDB (Vector Store), Ollama (Local LLM), Tavily (Web Search), Python

## **2. 현재까지 완료된 작업**

프로젝트의 핵심 데이터 처리 및 콘텐츠 생성 파이프라인 구축이 완료되었습니다.

* **src/config.py**: 프로젝트의 모든 경로, API 키, 모델 이름을 중앙에서 관리하는 설정 파일 구현 완료.
* **src/logger.py**: JSON 형식의 파일 로깅 및 콘솔 로깅을 위한 로거 모듈 구현 완료.
* **src/ingestion.py**: data/source_pdfs/ 디렉토리에서 PDF 문서를 로드하고 텍스트를 추출하여 의미 있는 단위(청크)로 분할하는 기능 구현 완료.
* **src/indexing.py**: 처리된 문서 청크를 임베딩하여 ChromaDB 벡터 스토어에 저장하는 인덱싱 파이프라인 구축 완료.
* **src/generation.py**: 로컬 벡터 스토어와 웹 검색 결과를 모두 활용하는 하이브리드 RAG 체인 구현 완료.
* **src/main.py**: 커맨드 라인에서 주제를 입력받아 전체 생성 파이프라인을 실행하고 결과를 파일로 저장하는 메인 스크립트 구현 완료.

## **3. 남은 작업 및 향후 계획 (To-Do)**

핵심 기능 구현 이후, 사용성 개선과 자동화, 안정성 확보를 위한 다음 작업들이 남아있습니다.

* **[ ] UI 개발 (src/ui/)**
  * Streamlit을 사용하여 사용자가 웹 인터페이스에서 직접 주제를 입력하고 생성된 블로그 포스트를 확인할 수 있는 UI를 개발합니다.
* **[ ] 자동 포스팅 에이전트 구현 (scripts/agent_script.py)**
  * 생성된 마크다운 콘텐츠를 GitHub 블로그나 다른 플랫폼에 자동으로 포스팅하는 LangChain 에이전트를 구현합니다.
  * scripts/tools.py의 post_to_github_blog 함수를 실제 GitHub 레포지토리와 연동하여 테스트하고 활성화합니다.
* **[ ] 단위 및 통합 테스트 작성 (tests/)**
  * pytest를 사용하여 각 모듈(ingestion, generation 등)의 기능이 올바르게 동작하는지 검증하는 단위 테스트를 추가합니다.
  * 전체 파이프라인이 예상대로 작동하는지 확인하는 통합 테스트를 작성하여 코드 안정성을 높입니다.
* **[ ] 모델 및 프롬프트 고도화**
  * 다양한 LLM 모델(e.g., Upstage Solar, GPT-4o-mini)을 테스트하여 결과물의 품질을 비교하고 최적의 모델을 선택합니다.
  * generation.py의 프롬프트 템플릿을 지속적으로 개선하여 더 나은 품질의 블로그 포스트를 생성하도록 유도합니다.
* **[ ] 문서화 개선**
  * 각 함수의 기능, 인자, 반환값 등을 설명하는 Docstring을 보강합니다.
  * 프로젝트의 전체 아키텍처와 설계 결정에 대한 내용을 docs/ 디렉토리에 추가합니다.

  _This log will now track the progress of experiments and key findings._
