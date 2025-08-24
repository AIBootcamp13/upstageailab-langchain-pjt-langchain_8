# src/main.py

# sqlite3 호환성을 위해 최상단에 추가
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import argparse
from pathlib import Path

from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_ollama import ChatOllama

from scripts.tools import post_to_github_blog
from src.config import LLM_MODEL, OUTPUT_DIR
from src.generation import BlogGenerator
from src.logger import get_logger

# 로거 초기화
logger = get_logger(__name__)


def extract_title(markdown_post: str) -> str:
    """마크다운 블로그 포스트에서 H1 제목을 추출합니다."""
    try:
        first_line = markdown_post.strip().split('\n')[0]
        if first_line.startswith('# '):
            return first_line[2:].strip()
        return "새 블로그 포스트"
    except IndexError:
        return "새 블로그 포스트"


def main(topic: str, publish: bool):
    """
    블로그 포스트를 생성하고 선택적으로 발행하는 메인 함수입니다.
    """
    logger.info(f"--- 주제: '{topic}'에 대한 블로그 포스트 생성을 시작합니다. ---")
    try:
        # 1. 블로그 포스트 생성
        generator = BlogGenerator()
        generated_post = generator.generate(topic)

        print("\n--- 생성된 블로그 포스트 ---\n")
        print(generated_post)

        # 2. 포스트를 로컬 파일에 저장
        file_name = topic.lower().replace(" ", "_").replace("'", "") + ".md"
        output_path = OUTPUT_DIR / file_name
        with output_path.open("w", encoding="utf-8") as f:
            f.write(generated_post)
        logger.info(f"✅ 블로그 포스트가 성공적으로 저장되었습니다: {output_path}")

# 3. --publish 플래그 사용 시, GitHub에 직접 포스팅
        if publish:
            logger.info("--- GitHub 블로그 포스팅을 시작합니다. ---")
            blog_title = extract_title(generated_post)
            
            # Correct Way: Use the .invoke() method with a dictionary
            tool_input = {"title": blog_title, "content": generated_post}
            result = post_to_github_blog.invoke(tool_input)
            
            logger.info(f"--- GitHub 포스팅 결과 --- \n{result}")

    except Exception as e:
        logger.error(f"블로그 생성 중 예상치 못한 오류 발생: {e}", exc_info=True)
        print("\n❌ 오류: 블로그 생성에 실패했습니다. 자세한 내용은 로그 파일을 확인해주세요.")


if __name__ == "__main__":
    # 커맨드 라인 인자 파싱 설정
    parser = argparse.ArgumentParser(description="RAG 기반 블로그 포스트 생성기")
    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="블로그 포스트의 주제를 입력하세요."
    )
    parser.add_argument(
        "--publish",
        action="store_true", # 이 인자를 플래그로 만듭니다 (예: --publish)
        help="이 플래그를 설정하면 생성된 포스트를 GitHub 블로그에 게시합니다."
    )
    args = parser.parse_args()

    main(args.topic, args.publish)