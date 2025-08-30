import subprocess
import sys
from pathlib import Path


def main():
    # 프로젝트 루트 기준 Streamlit 앱 경로
    app_path = Path("src/app.py").resolve()

    if not app_path.exists():
        print(f"[오류] Streamlit 앱 파일을 찾을 수 없습니다: {app_path}")
        sys.exit(1)

    # 현재 파이썬(poetry 가상환경)의 streamlit 모듈을 사용하도록 -m streamlit 사용
    # main.py 뒤에 붙인 추가 인자들은 그대로 Streamlit에 전달
    args = [sys.executable, "-m", "streamlit", "run", str(app_path), *sys.argv[1:]]
    try:
        completed = subprocess.run(args, check=False)  # noqa: S603
        sys.exit(completed.returncode)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
