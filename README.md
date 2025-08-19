# 프로젝트 이름

## 💻 프로젝트 소개

### <프로젝트 소개>

- W.I.P.

### <작품 소개>

- W.I.P.

## 👨‍👩‍👦‍👦 팀 구성원

| ![조의영](https://avatars.githubusercontent.com/u/4915390?v=4) | ![최웅비](https://avatars.githubusercontent.com/u/97170457?v=4) | ![고민주](https://avatars.githubusercontent.com/u/204635884?v=4) | ![박성진](https://avatars.githubusercontent.com/u/204808507?v=4) | ![조은별](https://avatars.githubusercontent.com/u/178245805?v=4) | ![김효석](https://avatars.githubusercontent.com/u/159979869?v=4) |
|:-----------------------------------------------------------:|:------------------------------------------------------------:|:-------------------------------------------------------------:|:-------------------------------------------------------------:|:-------------------------------------------------------------:|:-------------------------------------------------------------:|
|             [조의영](https://github.com/yuiyeong)              |              [최웅비](https://github.com/Wchoi189)              |             [고민주](https://github.com/PaperToCode)             |              [박성진](https://github.com/psj2024p)               |              [조은별](https://github.com/eunbyul2)               |            [김효석](https://github.com/david1005910)             |
|                         팀장, W.I.P.                          |                            W.I.P.                            |                            W.I.P.                             |                            W.I.P.                             |                            W.I.P.                             |                            W.I.P.                             |

## 🔨 개발 환경 및 기술 스택

**언어 및 프레임워크**

- 주 언어: Python 3.11.11
- Frontend: Streamlit (메인 UI)
- AI/ML: LangChain, LangGraph, LangSmith

**벡터 저장소**

- Vector DB: ChromaDB

**LLM APIs**

- OpenAI GPT Models
- Upstage API

**개발 도구**

- 패키지 관리: Poetry
- 버전 관리: Git, GitHub
- 코드 품질: Ruff, Pre-commit
- 개발 환경: JupyterLab, IPython

**협업 도구**

- GitHub (코드 관리, 이슈 트래킹)
- Notion (프로젝트 문서화)
- Slack, KakaoTalk (실시간 소통)

## 📁 프로젝트 구조

- W.I.P.

## 💻 구현 기능

- W.I.P.

## 🛠️ 작품 아키텍처

- W.I.P.

## Getting Started

### Cloud Instance 환경 설정 with Shell Script

**Python 버전과 의존성 관리자(Poetry) 및 Python 관련 설치 및 설정**

1. GPU 서버에 SSH 로 로그인한 다음, 아래 명령어를 입력하여 환경 설정 스크립트 다운로드합니다.
    ```bash
    wget https://gist.githubusercontent.com/yuiyeong/8ae3f167e97aeff90785a4ccda41e5fe/raw/bcf100f01b69df0534841f7cb126f96d307fc460/setup_env.sh
    ```

2. 다운로드 받은 스크립트를 실행 파일로 변경합니다.
    ```bash
    chmod +x setup_env.sh
    ```

3. 실행 파일을 실행합니다.
    ```bash
    ./setup_env.sh
    ```

**이 스크립트는 다음 내용을 설정합니다.**

- 시스템 업데이트 및 Python 빌드 의존성 설치
- /workspace 작업 디렉토리 생성
- Python 3.11 conda 환경 구성
- Poetry 설치 및 경로 설정
- 환경 변수 설정 (HOME, PATH, PYTHONPATH)
- SSH 로그인 시 자동 설정들

### 프로젝트 클론 및 의존성 설치

1. GPU 서버에 SSH 로 로그인한 다음, 아래 명령어로 이 Repository 를 Clone 합니다.
    ```bash
    git clone https://github.com/AIBootcamp13/upstageailab-langchain-pjt-langchain_8.git
    ```

2. 다음 명령어를 실행해서 프로젝트의 환경 설정을 마칩니다.
    ```bash
    cd upstageailab-langchain-pjt-langchain_8

    poetry install --extras dev
    poetry run pre-commit install
    ```

## 🚨 트러블 슈팅

- W.I.P.

## 📌 프로젝트 회고

- W.I.P.

## 📰 참고자료

- [Poetry](https://python-poetry.org/docs/)
- [Ruff](https://docs.astral.sh/ruff/)
- [Pre-commit](https://pre-commit.com/)
- [LangChain Documentation](https://python.langchain.com/docs/introduction/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/get-started)
- [OpenAI API Documentation](https://platform.openai.com/docs/overview)
- [Upstage Solar API](https://console.upstage.ai/docs/getting-started)
