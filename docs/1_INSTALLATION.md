# **💻 설치 가이드**

이 문서는 Blog Content Creator Agent 프로젝트를 로컬 환경에 설치하고 실행하는 방법을 안내합니다.

## **1. 사전 요구사항**

프로젝트를 실행하기 위해 다음 도구들이 설치되어 있어야 합니다.

* **Git**: 소스 코드를 내려받기 위한 버전 관리 시스템입니다.  
* **Anaconda / Miniconda**: Python 환경과 패키지를 관리하기 위한 배포판입니다. conda 명령어를 사용할 수 있어야 합니다.  
* **Poetry**: Python 의존성 관리를 위한 도구입니다.

## **2. 설치 절차**

### **단계 1: 프로젝트 저장소 복제 (Clone)**

터미널을 열고 다음 명령어를 실행하여 프로젝트 소스 코드를 컴퓨터로 복제합니다.

```bash
git clone [https://github.com/AIBootcamp13/upstageailab-langchain-pjt-langchain_8.git](https://github.com/AIBootcamp13/upstageailab-langchain-pjt-langchain_8.git)  
cd upstageailab-langchain-pjt-langchain_8
```
### **단계 2: Python 가상환경 생성 및 활성화**

프로젝트에 필요한 Python 3.11 버전의 conda 가상환경을 생성하고 활성화합니다.

## 'langchain-project'라는 이름의 Python 3.11.11 가상환경 생성
```bash  
conda create -n langchain-project python=3.11.11 -y
```
## 생성된 가상환경 활성화 
```bash
conda activate langchain-project
```
터미널 프롬프트 앞에 (langchain-project)가 표시되면 가상환경이 성공적으로 활성화된 것입니다.

### **단계 3: 의존성 패키지 설치**

**Poetry**를 사용하여 프로젝트에 필요한 모든 라이브러리를 설치합니다.

## Poetry 설치 (이미 설치되어 있다면 생략)
```bash  
pip install poetry
```
## 프로젝트 의존성 설치  
## --extras dev: Ruff, pre-commit 등 개발용 도구도 함께 설치 
```bash 
poetry install --extras dev
``` 
## Git commit 전 코드 스타일을 자동으로 검사/수정하는 pre-commit 설정  
```bash 
poetry run pre-commit install
``` 
### **단계 4: API 키 및 환경 변수 설정**

애플리케이션이 작동하려면 여러 외부 서비스의 API 키가 필요합니다.

1. 프로젝트의 루트 디렉터리에서 .env.template 파일을 .env 파일로 복사합니다. 
```bash  
   cp .env.template .env
``` 
2. 방금 생성한 .env 파일을 텍스트 편집기로 열고, 각 API 키 값을 채워 넣습니다.  
```bash 
   .env
``` 
   ## 1. OpenAI API 키  
   ### - [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys) 에서 발급
   ```bash   
   OPENAI_API_KEY="sk-..."
   ``` 
   ## 2. Upstage API 키  
   [문제해결 가이드](docs/6_TROUBLESHOOTING.md) 문서를 참고하세요.
