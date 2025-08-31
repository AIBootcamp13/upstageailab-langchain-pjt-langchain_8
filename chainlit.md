## Blog Content Generator — 블로그 초안 생성기

간단한 PDF 업로드로 기술 블로그 초안을 자동 생성하고, 실시간으로 스트리밍되는 출력물을 보며 즉시 편집할 수 있는 도구입니다.

⚡ 주요 특징

- PDF 업로드 → 문서 전처리 → 벡터화 → 리트리버 기반 RAG → 블로그 초안 생성
- 모델 프로필(설정)에서 LLM 선택 가능
- 스트리밍 출력(타이핑 효과) 및 사이드바 토큰 패널 제공
- 초안 수정/재생성/저장 워크플로 지원

---

English (short):

- PDF upload → preprocess → vectorize → retriever-based RAG → draft generation
- Choose LLM from model profiles in settings
- Streaming output (typing effect) and a token sidebar
- Draft edit / regenerate / save workflow supported

## 빠른 시작

1. 사이드바/우측 상단 설정(⚙️)에서 모델 프로필을 선택하세요. (예: OpenAI, Ollama 등)
2. 채팅 창에 PDF 파일을 업로드합니다. (PDF만 지원)
3. 업로드 후 자동으로 문서 처리가 진행되고 초안이 스트리밍됩니다.
4. 초안이 표시되면, 채팅 입력으로 수정 요청을 보내거나 `💾 초안 저장`을 사용하세요.

Quick Start (English):

1. Open the settings in the top-right and choose a model profile (e.g. OpenAI, Ollama).
2. Upload a PDF in the chat input. The system supports PDF files for document ingestion.
3. After upload the document will be processed and a draft will stream into the chat.
4. Edit inline or use the `💾 Save Draft` action to persist changes.

## 모델 프로필과 모드

- 모델 프로필: `configs/config.yaml`의 `profiles` 항목에서 정의됩니다. 친숙한 라벨은 `src/ui/chainlit/settings.py`의 `PROFILE_LABELS`에서 조정할 수 있습니다.
- 동작 모드: `Drafting`(초안 생성)과 `Editing`(초안 수정) 모드 전환을 지원합니다. 모드 설정은 채팅 시작 시 설정 패널에서 선택하세요.
- 프로필 변경 시(설정에서 선택) 문서가 이미 업로드되어 있으면 초안이 자동으로 재생성됩니다.

Model Profiles & Modes (English):

- Profiles are defined in `configs/config.yaml` under the `profiles` section. Labels can be adjusted in `src/ui/chainlit/settings.py`.
- Modes: `Drafting` and `Editing` are available from the settings panel shown at chat-start.
- When you change profiles and documents are already uploaded, the draft will auto-regenerate.

## 스트리밍 UX와 토큰 패널

- 스트리밍: 모델의 출력은 실시간으로 채팅에 타이핑되는 것처럼 표시됩니다(문자/토큰 단위).
- 토큰 패널: 토큰 사용 정보는 채팅에 자동으로 표시되지 않고, 우측 사이드바의 `Session Tokens`에서 확인할 수 있습니다.
	- 토큰 패널은 대화 메시지의 `📊 토큰 보기` 버튼으로 열 수 있습니다(토글).
	- 정확한 토큰 계산을 위해 `tiktoken`을 설치하세요: `poetry add tiktoken`.

	Streaming UX & Token Panel (English):

	- Streaming: model output is displayed in real-time with a typing effect (char/token granularity).
	- Token panel: use the `📊 View Tokens` button attached to a message to open the session token sidebar (toggle).
	- For exact token counting, install `tiktoken`: `poetry add tiktoken`.

## 예시 프롬프트

- "서론을 초심자 친화적으로 다시 써줘."
- "결론을 3문장으로 요약해줘."
- "이 섹션을 더 기술적으로, 예시 코드를 추가해서 확장해줘."

## 시각적 개선 제안

- 프로젝트 로고/아이콘: `README` 상단에 작은 스크린샷 혹은 GIF를 추가하면 스트리밍 UX를 보여주기 좋습니다.
- 버튼 아이콘: 저장(💾), 토큰(📊), 설정(⚙️) 같은 직관적 아이콘 사용을 유지하세요.
- 사이드바: 토큰 외에도 `요약`, `변경 이력`, `메타데이터` 탭을 만들어 배치하면 편리합니다.

---

## 문제 해결

- 프로필이 보이지 않음: Chainlit 버전 및 `configs/config.yaml`의 `profiles` 정의를 확인하세요.
- 스트리밍이 안 됨: 사용 중인 LLM이 스트리밍을 지원하는지 확인하고 `OPENAI_API_KEY` 또는 Ollama 설정을 확인하세요.
