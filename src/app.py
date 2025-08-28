from enum import Enum

import streamlit as st

from src.ui.components.contents_editor import ContentsEditor
from src.ui.components.file_uploader import FileUploader
from src.ui.components.github_auth import GithubAuthenticator
from src.ui.components.publisher import Publisher
from src.ui.enums import SessionKey


class AppStage(str, Enum):
    AUTH = "auth"
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
        if SessionKey.CURRENT_STAGE not in st.session_state:
            # 첫 번째 렌더링
            self._change_stage(AppStage.AUTH)

        current_stage = st.session_state[SessionKey.CURRENT_STAGE]
        if current_stage == AppStage.AUTH:
            self._render_auth_stage()
        elif current_stage == AppStage.UPLOAD:
            self._render_upload_stage()
        elif current_stage == AppStage.EDIT:
            self._render_edit_stage()
        elif current_stage == AppStage.PUBLISH:
            self._render_publish_stage()
        else:
            self._render_auth_stage()

    def _render_auth_stage(self):
        if self.github_authenticator.render():
            self._change_stage(AppStage.UPLOAD)

    def _render_upload_stage(self):
        if self.file_uploader.render():
            self._change_stage(AppStage.EDIT)

    def _render_edit_stage(self):
        if self.contents_editor.render():
            self._change_stage(AppStage.PUBLISH)

    def _render_publish_stage(self):
        if self.publisher.render():
            self._change_stage(AppStage.AUTH)

    def _change_stage(self, stage: AppStage):
        st.session_state[SessionKey.CURRENT_STAGE] = stage.value
        st.rerun()


if __name__ == "__main__":
    app = BlogCreatorApp()
    app.run()
