# src/config.py
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from icecream import ic


# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()


def find_project_root(marker: str = "pyproject.toml") -> Path:
    """
    'pyproject.toml' 파일을 기준으로 프로젝트의 루트 디렉토리를 찾습니다.
    """
    current_path = Path().resolve()
    while current_path != current_path.parent:
        if (current_path / marker).exists():
            return current_path
        current_path = current_path.parent
    raise FileNotFoundError(f"프로젝트 루트 마커 '{marker}'를 찾을 수 없습니다.")


def get_env_or_raise(key: str) -> str:
    """
    환경 변수를 가져오거나, 변수가 설정되지 않은 경우 예외를 발생시킵니다.
    """
    env_value = os.getenv(key)
    if not env_value:
        raise ValueError(f"필수 환경 변수 '{key}'가 설정되지 않았습니다.")
    return env_value


# --- 기본 경로 설정 ---
ROOT_DIR = find_project_root()
LOG_ROOT_DIR = ROOT_DIR / "logs"

# --- 상세 디렉토리 경로 ---
DATA_DIR = ROOT_DIR / "data"
SOURCE_PDFS_DIR = DATA_DIR / "source_pdfs"
VECTOR_STORE_DIR = ROOT_DIR / "vector_store"
OUTPUT_DIR = ROOT_DIR / "output"

# --- 시간대 설정 ---
TIMEZONE = ZoneInfo("Asia/Seoul")

# --- API 키 ---
# .env 파일에 키가 없으면 오류를 발생시킵니다.
OPENAI_API_KEY = get_env_or_raise("OPENAI_API_KEY")
UPSTAGE_API_KEY = get_env_or_raise("UPSTAGE_API_KEY")
# 웹 검색을 위한 Tavily API 키 (generation.py에서 사용)
TAVILY_API_KEY = get_env_or_raise("TAVILY_API_KEY")

# --- 모델 및 임베딩 설정 ---
# 여기서 모델을 쉽게 교체할 수 있습니다.
EMBEDDING_MODEL = "BAAI/bge-m3"  # 한국어 지원 및 고성능 모델
LLM_MODEL = "gpt-oss-20b"  # Ollama 로컬 모델

# --- 벡터 스토어 설정 ---
VECTOR_STORE_NAME = "chroma_db_blog_posts"
PERSIST_DIRECTORY = str(VECTOR_STORE_DIR / VECTOR_STORE_NAME)


def initialize_directories():
    """프로젝트에 필요한 모든 디렉토리를 생성합니다."""
    dirs = [
        LOG_ROOT_DIR,
        DATA_DIR,
        SOURCE_PDFS_DIR,
        VECTOR_STORE_DIR,
        OUTPUT_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


# 스크립트 로드 시 디렉토리 초기화 실행
initialize_directories()

if __name__ == "__main__":
    # 이 파일을 직접 실행하여 설정값이 올바르게 로드되었는지 확인할 수 있습니다.
    ic("Configuration Validation")
    ic(ROOT_DIR)
    ic(SOURCE_PDFS_DIR)
    ic(PERSIST_DIRECTORY)
    ic(OUTPUT_DIR)
    ic("OpenAI API Key Loaded", "Yes" if OPENAI_API_KEY else "No")
    ic("Upstage API Key Loaded", "Yes" if UPSTAGE_API_KEY else "No")
    ic("Tavily API Key Loaded", "Yes" if TAVILY_API_KEY else "No")
    ic(EMBEDDING_MODEL)
    ic(LLM_MODEL)
