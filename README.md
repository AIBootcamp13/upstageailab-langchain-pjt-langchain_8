# Blog Content Creator Agent

## 💻 프로젝트 소개

### 프로젝트 개요

PPT나 문서 자료를 입력받아 고품질 블로그 포스트를 자동 생성하고, 다양한 블로그 플랫폼에 자동으로 게시하는 LangChain 기반 자동화 시스템입니다.

### 주요 특징

- **Advanced RAG**: 다양한 chunking 전략으로 정확한 콘텐츠 생성
- **Hallucination 방지**: LangSmith 활용한 프롬프트 최적화
- **완전 자동화**: 자료 입력부터 블로그 발행까지 원클릭 처리
- **멀티 플랫폼**: 네이버 블로그, 티스토리 등 주요 플랫폼 지원

#### 핵심 기능

**Phase 1: 콘텐츠 생성**

- PPT/PDF 등 자료 입력 → Markdown 형식 블로그 초안 생성
- RAG 기술을 활용한 정확한 정보 추출 및 구조화

**Phase 2: 자동 게시**

- 생성된 콘텐츠를 블로그 플랫폼에 자동 게시
- 로그인 → 글 작성 → 저장/발행까지 완전 자동화

#### 활용 사례

- 회사 발표 자료 → 기술 블로그 포스트
- 강의 자료 → 학습 블로그 글
- 아이디어 메모 → 완성도 높은 콘텐츠

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

```
.
├── README.md                # 프로젝트 문서
├── pyproject.toml          # Poetry 의존성 관리
├── poetry.lock             # 의존성 버전 고정
├── ruff.toml              # 코드 포맷터 설정
├── docs/                   # 프로젝트 문서
│   ├── imgs/              # 문서용 이미지
│   └── project_guide.md   # 프로젝트 가이드
├── notebooks/             # Jupyter Notebook 실험
│   ├── psjin2024p/       # 개인 작업 공간
│   └── yuiyeong/         # 개인 작업 공간
├── scripts/               # 유틸리티 스크립트
│   └── init-instance.sh  # 인스턴스 초기화
└── src/                   # 소스 코드
    ├── __init__.py
    ├── main.py           # 메인 실행 파일
    ├── config.py         # 설정 관리
    ├── logger.py         # 로깅 모듈
    └── ui/               # UI 관련 모듈
        └── __init__.py
```

## 💻 구현 기능

- W.I.P.

## 🛠️ 작품 아키텍처

- W.I.P.

## 🚀 Getting Started

### Prerequisites

개발 환경을 설정하기 전에 다음 요구사항을 확인해주세요.

- Python 3.11.11을 사용하기 위해서 **Anaconda** 또는 **Miniconda**가 설치되어 있어야 합니다.
- 패키지 관리 도구인 **Poetry**가 설치되어 있어야 합니다.

만약 위 사항을 만족하지 못했다면, [Prerequisites 설정](#prerequisites-설정) 부분을 먼저 확인해주세요.

### 빠른 시작

#### **1. Python 환경 설정**

Conda를 사용하여 Python 3.11.11 환경을 생성합니다.

```bash
# Python 3.11.11 환경 생성
conda create -n langchain-project python=3.11.11 -y

# 환경 활성화
conda activate langchain-project
```

#### **2. Repository 클론**

```bash
git clone https://github.com/AIBootcamp13/upstageailab-langchain-pjt-langchain_8.git

cd upstageailab-langchain-pjt-langchain_8
```

#### **3. 의존성 설치**

```bash
poetry install --extras dev

poetry run pre-commit install
```

#### **4. 환경변수 설정**

API 키를 설정하기 위해 `.env` 파일을 생성합니다.

```bash
# .env.template을 복사하여 .env 파일 생성
cp .env.template .env
```

생성된 `.env` 파일을 편집하여 실제 API 키를 입력합니다.

```bash
# 텍스트 에디터로 .env 파일 편집 (예: nano, vim, code 등)
vi .env
```

`.env` 파일에 다음과 같이 실제 API 키를 입력합니다:

```
OPENAI_API_KEY=실제_openai_api_키를_여기에_입력
UPSTAGE_API_KEY=실제_upstage_api_키를_여기에_입력
```

### Prerequisites 설정

`Python 3.11.11`이나 `Poetry`가 설치되어 있지 않은 경우, 아래 환경별 가이드를 따라 설정해주세요.

#### Upstage Cloud Instance 환경 설정

터미널 또는 VS Code의 Remote SSH를 이용해 GPU 서버에 접속한 후, 다음 명령어를 실행합니다.

```bash
# 환경 설정 스크립트 다운로드 및 실행
wget https://gist.githubusercontent.com/yuiyeong/8ae3f167e97aeff90785a4ccda41e5fe/raw/bcf100f01b69df0534841f7cb126f96d307fc460/setup_env.sh
chmod +x setup_env.sh
./setup_env.sh
```

> **참고**: 중간에 TimeZone 설정 입력창이 나타나면,
> 1. `Asia` (6번) 선택
> 2. `Seoul` (69번) 선택

##### _VS Code Remote SSH 사용 시 추가 설정_

VS Code Remote SSH를 사용한 경우, 환경 설정 스크립트 실행 후 다음 명령어를 **한 번만** 실행해주세요.

```bash
pkill -f vscode-server
```

> **주의**: 위 명령어 실행 후 연결 끊김 에러가 발생할 수 있습니다. 이는 정상적인 과정이므로,
> 1. 에러 팝업을 닫습니다.
> 2. 모든 VS Code 창을 종료합니다.
> 3. VS Code를 다시 실행합니다.

#### 로컬 개발 환경 설정

##### 1. Anaconda/Miniconda 설치

- **Anaconda**가 이미 설치되어 있다면, 2번을 진행해주세요.

운영체제별로 [Anaconda 공식 설치 문서](https://docs.anaconda.com/anaconda/install/)를 참고하여 Anaconda 또는 Miniconda를 설치해주세요.

- **Windows**: [Windows 설치 가이드](https://docs.anaconda.com/anaconda/install/windows/)
- **macOS**: [macOS 설치 가이드](https://docs.anaconda.com/anaconda/install/mac-os/)
- **Linux**: [Linux 설치 가이드](https://docs.anaconda.com/anaconda/install/linux/)

##### 2. Python 3.11.11 환경 생성

Conda를 사용하여 Python 3.11.11 환경을 생성합니다.

```bash
# Python 3.11.11 환경 생성
conda create -n langchain-project python=3.11.11 -y

# 환경 활성화
conda activate langchain-project

# Python 버전 확인
python --version
```

##### 3. Poetry 설치

[Poetry 공식 설치 문서](https://python-poetry.org/docs/#installation)를 참고하여 Poetry를 설치해주세요.

**권장 설치 방법 (모든 운영체제 공통)**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Windows (PowerShell)**

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

설치 후 터미널을 재시작하고 확인

```bash
poetry --version
```

> **참고**: Poetry가 PATH에 추가되지 않은 경우, [공식 문서의 PATH 설정 가이드](https://python-poetry.org/docs/#add-poetry-to-your-path)를 참고해주세요.

## Git 사용 규칙

### 기본 작업 흐름

```bash
git switch main

git pull

git branch feature/some-branch

git switch feature/some-branch

# 작업 진행

git status

git add 작업한_파일

git commit -m "prefix: 커밋 메시지"
# prefix를 꼭 달아서 메시지를 작성합시다!

git push origin feature/some-branch

# GitHub에 들어가서 Pull Request(PR) 만들기
```

### Commit Message Convention

#### 1. Commit 제목

commit 제목은 commit을 설명하는 문장형이 아닌 구나 절의 형태로 작성

#### 2. Importance of Capitalize

importanceofcapitalize가 아닌 `Importance of Capitalize`

#### 3. Prefix 꼭 달기

**주요 Prefix:**

- `feat`: 기능 개발 관련
- `fix`: 오류 개선 혹은 버그 패치
- `docs`: 문서화 작업
- `test`: test 관련
- `conf`: 환경설정 관련
- `build`: 빌드 작업 관련
- `ci`: Continuous Integration 관련
- `chore`: 패키지 매니저, 스크립트 등
- `style`: 코드 포맷팅 관련

### Branch 이름 Convention

- **feature/[github 이슈 번호]-[기능명]** - 새로운 기능 개발 시 (예: feature/12-login-page)
- **fix/[github 이슈 번호]-[버그명]** - 버그 수정 시 (예: fix/3-header-alignment)
- **docs/[github 이슈 번호]-[문서명]** - 문서 관련 작업 시 (예: docs/4-api-guide)

### Pull Request 규칙

1. PR 제목은 작업 내용을 명확하게 설명
2. PR 설명에는 변경 사항과 테스트 방법 포함
3. 최소 1명 이상의 리뷰어 승인 필요
4. 모든 테스트 통과 후 머지

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
