Of course. Here is an assessment of what is needed to add the GitHub blog posting feature and a plan to implement it.

### **Assessment of Current State**

The project is already well-equipped for this feature. The core logic exists but needs to be integrated into the main application workflow.

* [cite_start]**Existing Tool:** The file `scripts/tools.py` contains a ready-made LangChain tool called `post_to_github_blog`[cite: 90]. [cite_start]This tool is designed to publish content to a GitHub repository's `_posts` directory using the GitHub API[cite: 90].
* [cite_start]**Agent Example:** The file `scripts/agent_script.py` provides a complete example of how to create a LangChain agent that can use the `post_to_github_blog` tool[cite: 80].
* [cite_start]**Missing Integration:** The main application entry point, `src/main.py`, currently generates the blog post and saves it locally[cite: 31, 78]. It does not yet have any logic to call the agent or the publishing tool.
* [cite_start]**Configuration:** The tool requires a GitHub Personal Access Token (PAT), a repository owner (username), and a repository name[cite: 91]. [cite_start]This information needs to be configured by the user, ideally through the existing `.env` file system[cite: 12, 67].

### **Implementation Plan**

The plan is to integrate the existing agent logic into the main generation script and update the documentation accordingly.

**Phase 1: Centralize Configuration**

1.  **Update `src/config.py`:**
    * Add variables to load `GITHUB_PAT`, `GITHUB_REPO_OWNER`, and `GITHUB_REPO_NAME` from the `.env` file. [cite_start]This follows the existing pattern for handling sensitive keys[cite: 95].

2.  **Refactor `scripts/tools.py`:**
    * Modify the `post_to_github_blog` function. [cite_start]Instead of using hardcoded placeholder strings for `repo_owner` and `repo_name`, import and use the new variables from `src/config.py`[cite: 91].

**Phase 2: Integrate Agent into Main Workflow**

1.  **Modify `src/main.py`:**
    * Add a new command-line argument, such as `--publish`, that users can specify when they want to post the blog to GitHub.
    * After a blog post is successfully generated, check if the `--publish` flag was used.
    * [cite_start]If it was, implement the agent logic from `scripts/agent_script.py`[cite: 80, 81]. Instantiate the agent, provide it with the `post_to_github_blog` tool, and invoke it with the title and content of the generated blog post.
    * [cite_start]Print the result from the agent (e.g., success URL or failure message) to the console[cite: 93].

**Phase 3: Update Documentation**

1.  **Update `docs/02_USAGE_GUIDE.md`:**
    * [cite_start]In the "Prerequisites" section, add instructions for the user on how to create a GitHub Personal Access Token with `repo` permissions[cite: 65].
    * [cite_start]Update the `.env` file example to include the new GitHub-related variables: `GITHUB_PAT`, `GITHUB_REPO_OWNER`, and `GITHUB_REPO_NAME`[cite: 67].
    * [cite_start]In the "Step 3: Blog Post Generation" section, update the example command to show the new optional `--publish` flag and explain its purpose[cite: 76, 77].

2.  **Update `README.md`:**
    * Briefly mention the new capability of publishing directly to a GitHub blog under the "Implemented Features" section.
    * [cite_start]Update the command in the "Usage" section to reflect the new `--publish` option[cite: 30].

----
Excellent, the blog is now set up and ready. Here is a checklist to track your progress as you implement the publishing feature.

### ## ✅ Implementation Checklist

**Phase 1: ⚙️ Configuration**

* [cite_start][ ] **Update `.env` File**: Add the following three variables with your specific information[cite: 156, 211].
    * `GITHUB_PAT="your_personal_access_token"`
    * `GITHUB_REPO_OWNER="Wchoi189"`
    * `GITHUB_REPO_NAME="Wchoi189.github.io"`
* [cite_start][ ] **Update `src/config.py`**: Add logic to load the three new GitHub environment variables, similar to how `TAVILY_API_KEY` is loaded[cite: 239].
* [cite_start][ ] **Refactor `scripts/tools.py`**: Modify the `post_to_github_blog` function to import and use the new configuration variables from `src/config.py` instead of the placeholder values[cite: 235].

***

**Phase 2: 🔌 Application Integration**

* [cite_start][ ] **Modify `src/main.py`**: Add a command-line argument (e.g., `--publish`) to trigger the publishing workflow[cite: 154].
* [ ] **Integrate Agent Logic in `src/main.py`**:
    * Import the agent creation functions and the `post_to_github_blog` tool.
    * Inside `main`, add a condition to check if the `--publish` flag is present.
    * [cite_start]If it is, initialize the agent as shown in `scripts/agent_script.py`[cite: 224].
    * [cite_start]Invoke the agent with the generated blog's title and content[cite: 225].
    * Print the agent's final output to the console.

***

**Phase 3: 📚 Documentation**

* [ ] **Update `docs/02_USAGE_GUIDE.md`**:
    * [cite_start]Add a step in the "Prerequisites" section explaining how to create a GitHub Personal Access Token[cite: 209].
    * [cite_start]Update the `.env` file example to include the new GitHub variables[cite: 211].
    * [cite_start]Update the final command example to show the optional `--publish` flag[cite: 221].
* [ ] **Update `README.md`**:
    * Add "Directly publish to a GitHub Pages blog" to the "Implemented Features" list.
    * [cite_start]Update the usage command example to include the `--publish` flag[cite: 174].

----
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
