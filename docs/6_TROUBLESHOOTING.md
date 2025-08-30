# **🐛 문제 해결 가이드 (Troubleshooting Guide)**

이 문서는 프로젝트를 설치하고 사용하면서 발생할 수 있는 일반적인 문제와 해결 방법을 안내합니다.

## **1. 설치 및 환경 문제**

### **Poetry 의존성 설치 실패 (poetry install)**

* **문제**: poetry install 명령어가 실패하며 패키지를 찾을 수 없다는 등의 오류가 발생합니다.  
* **해결 방법**:  
  1. **Python 버전 확인**: 시스템에 설치된 Python 버전이 3.11 이상인지 확인하세요. (python --version)  
  2. **Poetry 캐시 삭제**: poetry cache clear --all pypi 명령어로 캐시를 삭제한 후 다시 시도해보세요.  
  3. **pyproject.toml 파일 확인**: 파일이 손상되지 않았는지 확인합니다.

### **모듈을 찾을 수 없음 (ModuleNotFoundError)**

* **문제**: poetry run streamlit run src/main.py 실행 시 ModuleNotFoundError: No module named '...' 오류가 발생합니다.  
* **해결 방법**:  
  1. **가상 환경 활성화**: Poetry 가상 환경이 올바르게 활성화되었는지 확인하세요. poetry shell 명령어를 사용하여 가상 환경에 직접 진입한 후 streamlit run src/main.py를 실행해보는 것이 가장 확실합니다.  
  2. **의존성 재설치**: poetry install을 다시 실행하여 모든 패키지가 정상적으로 설치되었는지 확인합니다.

## **2. API 키 및 인증 오류**

### **API 키 설정 오류 (ValueError: ... not set)**

* **문제**: 애플리케이션 실행 시 ValueError: OPENAI_API_KEY not set in environment variables와 같은 오류가 발생합니다.  
* **해결 방법**:  
  1. 루트 디렉토리에 .env 파일이 있는지 확인하세요. 없다면 cp .env.template .env 명령어로 생성합니다.  
  2. .env 파일을 열어 OPENAI_API_KEY, TAVILY_API_KEY 등의 모든 필수 API 키가 올바르게 입력되었는지 확인하세요. = 뒤에 공백이 없어야 합니다.

### **GitHub 인증 실패**

* **문제**: GitHub Personal Access Token(PAT)으로 인증 시 오류가 발생합니다.  
* **해결 방법**:  
  * **"유효하지 않은 Personal Access Token입니다" (401 오류)**:  
    * GitHub에서 토큰이 만료되었거나 삭제되지 않았는지 확인하세요.  
    * .env 파일에 토큰을 복사/붙여넣기 할 때 오타가 없는지 다시 확인하세요.  
  * **"Repository에 대한 쓰기 권한이 없습니다" (403 오류)**:  
    * GitHub에서 PAT를 생성할 때 repo 스코프에 체크했는지 확인하세요. 권한이 없다면 토큰을 재발급해야 합니다.  
  * **"Repository를 찾을 수 없습니다" (404 오류)**:  
    * [your-username]/[your-username].github.io 형식의 저장소가 GitHub에 실제로 존재하는지 확인하세요.

## **3. 애플리케이션 실행 오류**

### **PDF 문서 처리 실패**

* **문제**: PDF 파일을 업로드했지만 처리 과정에서 멈추거나 오류가 발생합니다.  
* **해결 방법**:  
  1. **PDF 파일 확인**: 업로드하려는 PDF 파일이 손상되지 않았는지, 암호화되어 있지 않은지 확인하세요.  
  2. **파서 변경**: configs/config.yaml 파일의 ingestion.parser 값을 변경해보세요. local(PyMuPDF)이 기본값이지만, 복잡한 레이아웃의 PDF는 unstructured가 더 효과적일 수 있습니다.

### **AI 에이전트 응답이 느리거나 이상할 경우**

* **문제**: AI의 응답 속도가 매우 느리거나, 요청과 관련 없는 콘텐츠를 생성합니다.  
* **해결 방법**:  
  1. **모델 확인**: configs/config.yaml에서 현재 사용 중인 LLM을 확인하세요. 로컬 모델(high_gpu 프로필)은 시스템 사양에 따라 느릴 수 있습니다.  
  2. **청킹 설정 조정**: 문서의 내용이 너무 복잡하게 얽혀 있다면 config.yaml의 text_splitter.chunk_size 값을 줄여서 테스트해볼 수 있습니다.  
  3. **프롬프트 확인**: prompts/prompts.yaml의 프롬프트가 의도에 맞게 작성되었는지 확인하세요. 특히 update_prompt의 JSON 형식 지시문이 손상되지 않았는지 중요합니다.

### **디버그 모드로 실행하기**

* **상황**: 애플리케이션의 상세한 동작을 확인하거나 오류의 원인을 추적하고 싶을 때 사용합니다.  
* **해결 방법**: 터미널에서 아래 명령어를 실행하여 기존 Streamlit 프로세스를 강제 종료하고 디버그 로그 레벨로 재시작할 수 있습니다.  

```bash
  pkill -f 'streamlit run' || true; sleep 1; poetry run streamlit run src/app.py --logger.level=debug
```
  * pkill -f 'streamlit run': 실행 중인 모든 Streamlit 프로세스를 종료시킵니다.  
  * --logger.level=debug: Streamlit 로거를 디버그 레벨로 설정하여 터미널에 더 상세한 로그를 출력합니다.

## **4. 자주 묻는 질문 (FAQ)**

### **환경 프로필 커맨드 사용 방법 (ENV_PROFILE=high_gpu)**

* **Q: 환경 프로필을 변경하는 커맨드가 운영체제마다 다른가요?**  
  * A: 네, 환경 변수 설정 방식이 운영체제마다 다릅니다. 다음 표를 참고하여 본인의 운영체제에 맞는 명령어를 사용하세요.

| 운영체제           | 사용 예시                                                         |
|------------------|-------------------------------------------------------------------|
| Linux/macOS      | `ENV_PROFILE=high_gpu poetry run streamlit run src/main.py`       |
| Windows CMD      | `set ENV_PROFILE=high_gpu && poetry run streamlit run src/main.py`|
| Windows PowerShell | `$env:ENV_PROFILE="high_gpu"; poetry run streamlit run src/main.py` |

> **참고:**  
> - 환경 변수가 올바르게 전달되지 않으면 원하는 프로필이 적용되지 않습니다.  
> - 커맨드 입력 후, `configs/config.yaml`의 high_gpu 프로필이 실제로 적용되는지 로그 또는 출력에서 확인하세요.
> - poetry 환경이 활성화되어야 하며, streamlit 및 기타 의존 패키지가 poetry 환경에 설치되어 있어야 합니다.

**문제 해결:**
- 환경 변수가 main.py에서 정상적으로 읽히는지 확인하려면, main.py 상단에 다음 코드를 추가해 출력해볼 수 있습니다:
    ```python
    import os
    print("ENV_PROFILE:", os.environ.get("ENV_PROFILE"))
    ```
- 파일/경로가 올바른지 확인하세요 (`src/main.py` 경로에 파일이 있어야 합니다).
- poetry 환경에서 streamlit이 설치되어 있어야 하며, 필요시 `poetry add streamlit`으로 추가하세요.

* **Q: PDF 외에 다른 파일(예: DOCX, PPTX)도 사용할 수 있나요?**  
  * A: 현재 버전은 PDF 파일만 공식적으로 지원합니다. 다른 파일 형식을 지원하려면 src/document_preprocessor.py에 해당 파일에 맞는 LangChain 로더를 추가해야 합니다.  
* **Q: AI의 글쓰기 스타일을 바꾸고 싶습니다.**  
  * A: prompts/prompts.yaml 파일의 draft_prompt에 있는 [Identity]와 [Instructions] 부분을 수정하여 AI의 역할과 작업 방식을 변경할 수 있습니다. 자세한 내용은 [설정 및 커스터마이징 가이드](4_CUSTOMIZATION.md)를 참고하세요.
