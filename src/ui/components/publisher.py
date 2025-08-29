import re
from datetime import datetime

import streamlit as st
from github import GithubException

from src.config import TIMEZONE
from src.ui.enums import SessionKey


class Publisher:
    STATUS_UNAUTHORIZED_CODE = 401
    STATUS_NOT_ALLOWED_CODE = 403
    STATUS_NOT_FOUND_CODE = 404

    FORMAT_DATE = "%Y-%m-%d"
    FORMAT_DATETIME = "%Y-%m-%d %H:%M:%S %z"
    POSTS_FOLDER = "_posts"

    def __init__(self):
        self.categories = ["기술", "라이프스타일", "여행", "요리", "비즈니스", "학습", "프로젝트"]
        self.tags = [
            "Python",
            "LangChain",
            "AI",
            "머신러닝",
            "딥러닝",
            "RAG",
            "패스트캠퍼스",
            "패스트캠퍼스AI부트캠프",
            "업스테이지패스트캠퍼스",
            "UpstageAILab",
            "국비지원",
            "패스트캠퍼스업스테이지에이아이랩",
            "패스트캠퍼스업스테이지부트캠프",
            "기록",
            "계획",
            "AI부트캠프13기",
            "GitHub",
            "Jekyll",
            "블로그",
            "개발일기",
        ]

    @property
    def github_client(self):
        return st.session_state.get(SessionKey.GITHUB_CLIENT)

    @property
    def github_repo_name(self) -> str:
        return st.session_state.get(SessionKey.GITHUB_REPO)

    @property
    def blog_post(self) -> str:
        return st.session_state.get(SessionKey.BLOG_POST, "")

    @property
    def is_published(self) -> bool:
        return st.session_state.get(SessionKey.IS_PUBLISHED, False)

    @is_published.setter
    def is_published(self, value: bool):
        st.session_state[SessionKey.IS_PUBLISHED] = value

    def render(self) -> bool:
        """Publisher UI 렌더링"""
        st.subheader("📝 블로그 포스트 발행")

        # 블로그 포스트 제목 입력
        post_title = st.text_input(
            "글 제목을 작성해주세요.",
            placeholder="예: LangChain으로 RAG 시스템 구축하기",
            help="제목은 파일명에도 사용됩니다",
        )
        category = st.selectbox("카테고리를 선택하세요", self.categories)
        tags = st.multiselect("태그를 선택하세요", self.tags, default=["Python"], help="여러 개 선택 가능")

        # 미리보기
        st.divider()
        st.markdown("### 📄 포스트 미리보기")

        # 본문 미리보기
        with st.container(height=500):
            if self.blog_post:
                st.markdown(self.blog_post)
            else:
                st.info("⚠️ 아직 생성된 블로그 포스트가 없습니다.")

        # 발행 버튼
        st.divider()

        is_publishable = post_title and category and tags and self.blog_post
        if st.button("🚀 GitHub Pages에 발행", type="primary", disabled=(not is_publishable), use_container_width=True):
            with st.spinner("발행 중..."):
                self.is_published = self._publish(post_title, category, tags)
                if self.is_published:
                    st.balloons()

        if self.is_published and st.button("또 다른 글 작성하기"):
            self._clear_post_data()
            return True

        return False

    def _make_jekyll_post_file_name(self, simple_name: str) -> str:
        """Jekyll 포스트 파일 이름 생성 (예: YYYY-MM-DD-title.md)"""
        date_part = datetime.now(TIMEZONE).strftime(self.FORMAT_DATE)

        # 한글과 특수문자를 처리하여 URL-safe한 파일명 생성
        # 영문, 숫자, 하이픈만 남기고 나머지는 제거
        title_part = re.sub(r"[^a-zA-Z0-9가-힣\s-]", "", simple_name)
        # 공백을 하이픈으로 변경
        title_part = re.sub(r"\s+", "-", title_part.strip())
        # 연속된 하이픈을 하나로
        title_part = re.sub(r"-+", "-", title_part)
        # 소문자로 변환
        title_part = title_part.lower()

        # 빈 문자열이 되었다면 기본값 사용
        if not title_part:
            title_part = "untitled-post"

        return f"{date_part}-{title_part}.md"

    def _make_front_matter(self, title: str, categories: list[str], tags: list[str]) -> str:
        """Jekyll Front Matter 생성"""
        date = datetime.now(TIMEZONE).strftime(self.FORMAT_DATETIME)
        front_matter_lines = [
            "---",
            f'title: "{title}"',
            f"date: {date}",
            f"categories: [{', '.join(categories)}]",
            f"tags: [{', '.join(tags)}]",
            "toc: true",
            "comments: false",
            "mermaid: true",
            "math: true",
            "---",
        ]
        return "\n".join(front_matter_lines)

    def _publish(self, post_title: str, category: str, tags: list[str]) -> bool:
        """GitHub Pages repository에 블로그 포스트 발행"""
        # 1. 포스트 콘텐츠 생성
        post_content = self._make_front_matter(post_title, [category], tags)
        post_content += "\n\n"  # Front Matter와 본문 사이 빈 줄 추가
        post_content += self.blog_post

        # 2. 파일명 생성
        file_name = self._make_jekyll_post_file_name(post_title)
        file_path = f"{self.POSTS_FOLDER}/{file_name}"

        try:
            # 3. GitHub repository 가져오기
            if not self.github_client or not self.github_repo_name:
                st.error("❌ GitHub 인증 정보가 없습니다. 다시 로그인해주세요.")
                return False

            repo = self.github_client.get_repo(self.github_repo_name)

            # 4. 파일 생성
            repo.create_file(path=file_path, message=f"feat: Create New Blog Post: {post_title}", content=post_content)
            st.success(f"✅ 블로그 포스트가 발행되었습니다: {file_name}")

            # 5. 블로그 URL 표시
            username = self.github_repo_name.split("/")[0]
            # public posts path usually drops the leading underscore from the folder name
            public_posts_path = self.POSTS_FOLDER.lstrip("_").rstrip("/")
            # derive slug by removing date prefix (YYYY-MM-DD-) and file extension
            try:
                slug = file_name[11:-3]
            except Exception:
                # fallback: remove extension and any leading date-like prefix
                slug = file_name.rsplit(".", 1)[0]
                if slug.count("-") >= 3:
                    slug = "-".join(slug.split("-")[3:])

            blog_url = f"https://{username}.github.io/{public_posts_path}/{slug}/"
            st.info(f"📝 블로그 포스트 URL: {blog_url}")
            st.caption("⏰ GitHub Pages 반영까지 몇 분 소요될 수 있습니다.")
            return True
        except GithubException as e:
            st.error(f"❌ GitHub 업로드 실패: {e!s}")
            return False
        except Exception as e:
            st.error(f"❌ 예기치 않은 오류: {e!s}")
            return False

    def _clear_post_data(self):
        del st.session_state[SessionKey.VECTOR_STORE]
        del st.session_state[SessionKey.RETRIEVER]
        del st.session_state[SessionKey.BLOG_DRAFT]
        del st.session_state[SessionKey.BLOG_POST]
        del st.session_state[SessionKey.BLOG_CREATOR_AGENT]
        del st.session_state[SessionKey.MESSAGE_LIST]
        del st.session_state[SessionKey.IS_PUBLISHED]
