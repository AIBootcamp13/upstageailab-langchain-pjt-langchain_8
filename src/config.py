# src/config.py
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from dotenv import load_dotenv
from icecream import ic

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

def find_project_root(marker: str = "pyproject.toml") -> Path:
    """'pyproject.toml' 파일을 기준으로 프로젝트의 루트 디렉토리를 찾습니다."""
    current_path = Path().resolve()
    while current_path != current_path.parent:
        if (current_path / marker).exists():
            return current_path
        current_path = current_path.parent
    raise FileNotFoundError(f"프로젝트 루트 마커 '{marker}'를 찾을 수 없습니다.")

def get_env_or_raise(key: str) -> str:
    """환경 변수를 가져오거나, 변수가 설정되지 않은 경우 예외를 발생시킵니다."""
    env_value = os.getenv(key)
    if not env_value:
        raise ValueError(f"필수 환경 변수 '{key}'가 설정되지 않았습니다.")
    return env_value

def load_config_from_yaml(config_path: Path) -> dict:
    """YAML 파일에서 설정을 로드합니다."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"설정 파일 '{config_path}'를 찾을 수 없습니다.")

# --- 기본 경로 설정 ---
ROOT_DIR = find_project_root()
LOG_ROOT_DIR = ROOT_DIR / "logs"

# --- YAML 설정 로드 ---
CONFIG = load_config_from_yaml(ROOT_DIR / "configs" / "config.yaml")

# --- 상세 디렉토리 경로 ---
DATA_DIR = ROOT_DIR / "data"
SOURCE_PDFS_DIR = DATA_DIR / "source_pdfs"
VECTOR_STORE_DIR = ROOT_DIR / "vector_store"

# It defaults to "output" if not specified in the YAML.
OUTPUT_DIR_NAME = CONFIG.get("paths", {}).get("output_dir", "output")
OUTPUT_DIR = ROOT_DIR / OUTPUT_DIR_NAME

# --- 시간대 설정 ---
TIMEZONE = ZoneInfo("Asia/Seoul")

# --- API 키 (from .env) ---
OPENAI_API_KEY = get_env_or_raise("OPENAI_API_KEY")
UPSTAGE_API_KEY = get_env_or_raise("UPSTAGE_API_KEY")
TAVILY_API_KEY = get_env_or_raise("TAVILY_API_KEY")
GITHUB_PAT = get_env_or_raise("GITHUB_PAT")
GITHUB_REPO_OWNER = get_env_or_raise("GITHUB_REPO_OWNER")
GITHUB_REPO_NAME = get_env_or_raise("GITHUB_REPO_NAME")

# --- 모델 및 임베딩 설정 (from config.yaml) ---
EMBEDDING_MODEL = CONFIG["models"]["embedding"]
LLM_MODEL = CONFIG["models"]["llm"]

# --- 벡터 스토어 설정 (from config.yaml) ---
VECTOR_STORE_NAME = CONFIG["vector_store"]["name"]
PERSIST_DIRECTORY = str(VECTOR_STORE_DIR / VECTOR_STORE_NAME)

RETRIEVAL_LOCAL_K = CONFIG["retrieval"]["local_k"]
RETRIEVAL_WEB_K = CONFIG["retrieval"]["web_k"]

INGESTION_CHUNK_SIZE = CONFIG["ingestion"]["chunk_size"]
INGESTION_CHUNK_OVERLAP = CONFIG["ingestion"]["chunk_overlap"]

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
    ic("Configuration Validation")
    ic(ROOT_DIR)
    ic(SOURCE_PDFS_DIR)
    ic(PERSIST_DIRECTORY)
    ic(OUTPUT_DIR)
    ic("OpenAI API Key Loaded:", "Yes" if OPENAI_API_KEY else "No")
    ic("EMBEDDING_MODEL:", EMBEDDING_MODEL)
    ic("LLM_MODEL:", LLM_MODEL)
    ic("VECTOR_STORE_NAME:", VECTOR_STORE_NAME)