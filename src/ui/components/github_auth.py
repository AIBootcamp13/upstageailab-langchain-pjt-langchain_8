# src/ui/components/github_auth.py

import streamlit as st
from github import Github, GithubException

from src.ui.enums import SessionKey


class GithubAuthenticator:
    """사이드바에 표시되는 GitHub 인증 및 상태 관리 클래스입니다."""

    STATUS_UNAUTHORIZED_CODE = 401
    STATUS_NOT_ALLOWED_CODE = 403
    STATUS_NOT_FOUND_CODE = 404

    def render(self):
        """사이드바에 인증 UI를 렌더링합니다."""
        st.subheader("🔐 GitHub 인증")

        # --- MODIFIED: 로그인 흐름 개선 ---
        # 1. 이미 인증된 경우, 로그인 정보와 로그아웃 버튼을 표시합니다.
        if SessionKey.GITHUB_CLIENT in st.session_state:
            self._render_authenticated_view()
            return
        
        # 2. 인증되지 않은 경우, 로그인 폼을 표시합니다.
        # st.expander를 사용하여 UI를 깔끔하게 유지합니다.
        with st.expander("GitHub에 로그인하여 포스트 발행하기", expanded=False):
            self._render_login_form()
        # --------------------------------

    def _render_authenticated_view(self):
        """사용자가 인증되었을 때의 UI를 렌더링합니다."""
        username = st.session_state.get(SessionKey.GITHUB_USERNAME, "N/A")
        repo = st.session_state.get(SessionKey.GITHUB_REPO, "N/A")
        st.success(f"✅ 로그인됨: @{username}")
        st.caption(f"연결된 Repository: {repo}")

        if st.button("로그아웃", use_container_width=True):
            self._clear_session_state()
            st.rerun()

    def _render_login_form(self):
        """로그인에 필요한 입력 필드와 버튼을 렌더링합니다."""
        github_pat = st.text_input(
            "GitHub Personal Access Token (PAT)",
            type="password",
            help="Settings → Developer settings → Personal access tokens에서 생성",
        )
        github_username = st.text_input(
            "GitHub Username", placeholder="예: langster", help="GitHub 프로필에 표시되는 사용자명"
        )

        if st.button(
            "인증하기", type="primary", disabled=not (github_pat and github_username), use_container_width=True
        ) and self._authenticate_github(github_pat, github_username):
            st.rerun()

    def _authenticate_github(self, github_pat: str, github_username: str) -> bool:
        # 이 메서드의 로직은 변경되지 않습니다.
        try:
            github_client = Github(github_pat)
            github_user = github_client.get_user()
            actual_username = github_user.login

            if actual_username.lower() != github_username.lower():
                st.warning(f"⚠️ 입력한 username({github_username})과 토큰 소유자({actual_username})가 다릅니다.")
                st.info(f"토큰 소유자 계정({actual_username})으로 진행합니다.")
        except GithubException as e:
            if e.status == self.STATUS_UNAUTHORIZED_CODE:
                st.error("❌ 유효하지 않은 Personal Access Token입니다.")
            else:
                st.error(f"❌ 인증 확인 실패: {e!s}")
            return False

        repository_name = f"{actual_username}/{actual_username}.github.io"
        try:
            repository = github_client.get_repo(repository_name)
            if not repository.permissions.push:
                st.error(f"❌ Repository '{repository_name}'에 대한 쓰기 권한이 없습니다.")
                st.info("토큰에 repo 권한이 있는지 확인해주세요.")
                return False
        except GithubException as e:
            if e.status == self.STATUS_NOT_FOUND_CODE:
                st.error(f"❌ Repository '{repository_name}'을 찾을 수 없습니다.")
                st.info("Repository 이름과 권한을 확인해주세요.")
            elif e.status == self.STATUS_NOT_ALLOWED_CODE:
                st.error("❌ Repository에 접근할 권한이 없습니다.")
                st.info("토큰에 repo 권한이 있는지 확인해주세요.")
            else:
                st.error(f"❌ Repository 접근 실패: {e!s}")
                return False

        st.session_state[SessionKey.GITHUB_CLIENT] = github_client
        st.session_state[SessionKey.GITHUB_PAT] = github_pat
        st.session_state[SessionKey.GITHUB_REPO] = repository_name
        st.session_state[SessionKey.GITHUB_USERNAME] = actual_username

        st.success("✅ GitHub 인증 성공!")
        return True

    def _clear_session_state(self):
        """인증 관련 세션 상태 키를 모두 제거합니다."""
        st.session_state.pop(SessionKey.GITHUB_CLIENT, None)
        st.session_state.pop(SessionKey.GITHUB_PAT, None)
        st.session_state.pop(SessionKey.GITHUB_REPO, None)
        st.session_state.pop(SessionKey.GITHUB_USERNAME, None)