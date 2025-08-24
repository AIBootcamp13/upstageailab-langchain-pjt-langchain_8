# src/main.py
import argparse
from pathlib import Path

from src.config import ROOT_DIR
from src.generation import BlogGenerator
from src.logger import get_logger


# 로거 초기화
logger = get_logger(__name__)


def main(topic: str):
    """
    주어진 주제에 대한 블로그 포스트 생성의 전체 과정을 실행합니다.

    Args:
        topic (str): 생성할 블로그 포스트의 주제.
    """
    logger.info(f"--- 주제: '{topic}'에 대한 블로그 포스트 생성을 시작합니다. ---")
    try:
        # 1. BlogGenerator 인스턴스 생성
        generator = BlogGenerator()

        # 2. 블로그 포스트 생성
        generated_post = generator.generate(topic)

        # 3. 결과 출력 및 저장
        print("\n--- 생성된 블로그 포스트 ---\n")
        print(generated_post)

        # 생성된 포스트를 파일로 저장
        output_dir = ROOT_DIR / "output"
        output_dir.mkdir(exist_ok=True)
        # 파일 이름으로 사용하기 어려운 문자 제거
        safe_topic = "".join(c for c in topic if c.isalnum() or c in " _-").rstrip()
        file_name = safe_topic.lower().replace(" ", "_") + ".md"
        output_path = output_dir / file_name

        with Path(output_path).open("w", encoding="utf-8") as f:
            f.write(generated_post)

        logger.info(f"--- 블로그 포스트가 다음 경로에 저장되었습니다: {output_path} ---")
        print(f"\n✅ 블로그 포스트가 성공적으로 저장되었습니다: {output_path}")

    except FileNotFoundError as e:
        logger.error(f"오류: {e}")
        print("\n❌ 오류: 벡터 스토어를 찾을 수 없습니다. 'src/indexing.py'를 먼저 실행하여 인덱스를 생성해주세요.")
    except Exception as e:
        logger.error(f"블로그 생성 중 예상치 못한 오류 발생: {e}", exc_info=True)
        print("\n❌ 오류: 블로그 생성에 실패했습니다. 자세한 내용은 로그 파일을 확인해주세요.")


if __name__ == "__main__":
    # 커맨드 라인 인자 파서 설정
    parser = argparse.ArgumentParser(description="RAG 기반 블로그 포스트 생성기")
    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="생성할 블로그 포스트의 주제를 입력하세요.",
    )
    args = parser.parse_args()

    # 메인 함수 실행
    main(topic=args.topic)
