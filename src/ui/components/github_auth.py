import streamlit as st
from github import Github, GithubException

from src.ui.enums import SessionKey


class GithubAuthenticator:
    """GitHub 인증 및 Repository 접근 권한 확인 클래스"""

    STATUS_UNAUTHORIZED_CODE = 401
    STATUS_NOT_ALLOWED_CODE = 403
    STATUS_NOT_FOUND_CODE = 404

    def render(self) -> bool:
        st.subheader("🔐 GitHub 인증")

        # 이미 인증된 경우
        if SessionKey.GITHUB_CLIENT in st.session_state:
            # --- FIX: Use the correct session key for the username ---
            st.success(f"✅ GitHub 계정 연결됨: @{st.session_state.get(SessionKey.GITHUB_USERNAME, 'N/A')}")
            st.info(f"📝 블로그 Repository: {st.session_state[SessionKey.GITHUB_REPO]}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("다음 단계로 →", type="primary", use_container_width=True):
                    return True
            with col2:
                if st.button("다시 로그인", use_container_width=True):
                    self._clear_session_state()
                    st.rerun()
            return False

        github_pat = st.text_input(
            "GitHub Personal Access Token (PAT)",
            type="password",
            help="Settings → Developer settings → Personal access tokens에서 생성",
        )
        github_username = st.text_input(
            "GitHub Username", placeholder="예: langster", help="GitHub 프로필에 표시되는 사용자명"
        )

        if st.button(
            "인증하기", type="primary", disabled=not (github_pat and github_username)
        ) and self._authenticate_github(github_pat, github_username):
            st.rerun()
        return False

    def _authenticate_github(self, github_pat: str, github_username: str) -> bool:
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

        # update state
        st.session_state[SessionKey.GITHUB_CLIENT] = github_client
        st.session_state[SessionKey.GITHUB_PAT] = github_pat
        st.session_state[SessionKey.GITHUB_REPO] = repository_name
        # --- FIX: Store the authenticated user's login name ---
        st.session_state[SessionKey.GITHUB_USERNAME] = actual_username

        st.success("✅ GitHub 인증 성공!")
        return True

    def _clear_session_state(self):
        """Clears authentication-related keys from the session state."""
        st.session_state.pop(SessionKey.GITHUB_CLIENT, None)
        st.session_state.pop(SessionKey.GITHUB_PAT, None)
        st.session_state.pop(SessionKey.GITHUB_REPO, None)
        st.session_state.pop(SessionKey.GITHUB_USERNAME, None)

