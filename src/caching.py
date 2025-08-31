# src/caching.py
import langchain
from langchain_redis import RedisCache
import redis  # redis.exceptions.ConnectionError를 위해 import 유지
from src.config import REDIS_HOST, REDIS_PORT

def setup_caching():
    """
    Redis를 LangChain의 글로벌 LLM 캐시로 설정합니다.

    이 함수는 Redis 서버에 연결을 시도하고, 성공하면
    LangChain의 전역 캐시로 설정합니다. 연결에 실패하더라도
    오류를 출력하고 애플리케이션 실행은 계속됩니다.
    """
    try:
        redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}"
        
        # --- MODIFIED: 사용자의 제안을 반영하여 redis_url 인자를 직접 사용합니다. ---
        # 이 방식은 라이브러리가 내부적으로 연결을 관리하도록 하여 더 안정적입니다.
        langchain.llm_cache = RedisCache(redis_url=redis_url)
        
        # 캐시 객체를 통해 내부 클라이언트에 접근하여 연결을 테스트합니다.
        langchain.llm_cache.redis.ping()
        
        print(f"✅ Redis 캐시가 성공적으로 연결되었습니다. (서버: {redis_url})")

    except redis.exceptions.ConnectionError as e:
        print(f"⚠️ Redis 서버에 연결할 수 없습니다. 캐싱이 비활성화됩니다. (서버: {redis_url})")
        print(f"   오류: {e}")
        langchain.llm_cache = None
    except Exception as e:
        print(f"❌ Redis 캐시 설정 중 예기치 않은 오류가 발생했습니다: {e}")
        langchain.llm_cache = None

