# src/app.py

import streamlit as st
from enum import Enum
from src.config import CONFIG
from src.caching import setup_caching
from src.ui.components.contents_editor import ContentsEditor
from src.ui.components.file_uploader import FileUploader
from src.ui.components.github_auth import GithubAuthenticator
from src.ui.components.publisher import Publisher
from src.ui.enums import SessionKey


class AppStage(str, Enum):
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
        self._render_sidebar()
        if SessionKey.CURRENT_STAGE not in st.session_state:
            self._change_stage(AppStage.UPLOAD)
        current_stage = st.session_state[SessionKey.CURRENT_STAGE]
        if current_stage == AppStage.UPLOAD:
            self._render_upload_stage()
        elif current_stage == AppStage.EDIT:
            self._render_edit_stage()
        elif current_stage == AppStage.PUBLISH:
            self._render_publish_stage()

    def _render_sidebar(self):
        """사이드바에 인증 및 모델 선택 컴포넌트를 렌더링합니다."""
        with st.sidebar:
            self.github_authenticator.render()
            st.divider()
            st.subheader("🤖 LLM 모델 선택")
            
            # --- MODIFIED: Logic to preserve dropdown state ---
            providers = list(CONFIG.get("llm_providers", {}).keys())
            
            # 현재 세션에 저장된 provider의 인덱스를 계산합니다.
            try:
                provider_index = providers.index(st.session_state.get("selected_llm_provider"))
            except ValueError:
                provider_index = 0 # 없을 경우 기본값

            selected_provider = st.selectbox(
                label="LLM 제공자 선택",
                options=providers,
                index=provider_index, # 계산된 인덱스를 사용해 선택 상태를 유지합니다.
                key="selected_provider"
            )
            
            if selected_provider:
                models = CONFIG["llm_providers"][selected_provider]
                
                # 현재 세션에 저장된 model의 인덱스를 계산합니다.
                try:
                    model_index = models.index(st.session_state.get("selected_llm_model"))
                except ValueError:
                    model_index = 0 # 없을 경우 기본값
                
                selected_model = st.selectbox(
                    label="상세 모델 선택",
                    options=models,
                    index=model_index, # 계산된 인덱스를 사용해 선택 상태를 유지합니다.
                    key="selected_model"
                )
                
                st.session_state["selected_llm_provider"] = selected_provider
                st.session_state["selected_llm_model"] = selected_model
                
                st.caption(f"Provider: `{selected_provider}` | Model: `{selected_model}`")
            # ----------------------------------------------------

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
    setup_caching()
    app = BlogCreatorApp()
    app.run()