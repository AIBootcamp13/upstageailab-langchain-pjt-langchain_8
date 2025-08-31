# src/app.py
# Streamlit UI

from enum import Enum

import streamlit as st
from src.caching import setup_caching
from src.ui.components.contents_editor import ContentsEditor
from src.ui.components.file_uploader import FileUploader
from src.ui.components.github_auth import GithubAuthenticator
from src.ui.components.publisher import Publisher
from ui.enums import SessionKey


class AppStage(str, Enum):
    # 'AUTH' 단계를 제거하고 'UPLOAD'를 시작점으로 변경합니다.
    UPLOAD = "upload"
    EDIT = "edit"
    PUBLISH = "publish"


class BlogCreatorApp:
    """
    BlogCreatorAgent 를 활용할 수 있는 UI 클래스
    """

    def __init__(self):
        st.set_page_config(
            page_title="블로그 글 생성기",
            page_icon="✏️",
            layout="wide",
        )

        st.title("📝 블로그 글 생성기")

        self.github_authenticator = GithubAuthenticator()
        self.file_uploader = FileUploader()
        self.contents_editor = ContentsEditor()
        self.publisher = Publisher()

    def run(self):
        # --- UI 변경: 사이드바를 먼저 렌더링합니다 ---
        self._render_sidebar()

        if SessionKey.CURRENT_STAGE not in st.session_state:
            # 첫 번째 렌더링 시, UPLOAD 단계에서 시작합니다.
            self._change_stage(AppStage.UPLOAD)

        current_stage = st.session_state[SessionKey.CURRENT_STAGE]

        # 메인 화면의 각 단계를 렌더링합니다.
        if current_stage == AppStage.UPLOAD:
            self._render_upload_stage()
        elif current_stage == AppStage.EDIT:
            self._render_edit_stage()
        elif current_stage == AppStage.PUBLISH:
            self._render_publish_stage()

    def _render_sidebar(self):
        """사이드바에 인증 컴포넌트를 렌더링합니다."""
        with st.sidebar:
            self.github_authenticator.render()
            st.divider()
            # 추후 모델 선택과 같은 다른 사이드바 요소가 여기에 추가될 수 있습니다.

    def _render_upload_stage(self):
        if self.file_uploader.render():
            self._change_stage(AppStage.EDIT)

    def _render_edit_stage(self):
        if self.contents_editor.render():
            self._change_stage(AppStage.PUBLISH)

    def _render_publish_stage(self):
        if self.publisher.render():
            self._change_stage(AppStage.UPLOAD)

    def _change_stage(self, stage: AppStage):
        st.session_state[SessionKey.CURRENT_STAGE] = stage.value
        st.rerun()


if __name__ == "__main__":
    # 앱이 실행될 때 가장 먼저 캐시 설정을 시도합니다.
    setup_caching()
    app = BlogCreatorApp()
    app.run()

