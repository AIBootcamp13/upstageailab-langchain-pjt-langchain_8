import streamlit as st


class Publisher:
    # TODO Github Pages 에 jekyll post 를 올릴 수 있는 기능을 구현해야함

    def render(self) -> bool:
        st.markdown("""
            - **굵은 글씨**
            - *기울임체*
            - `코드 하이라이트`
            - [링크](https://streamlit.io)

            수식도 지원한다:
            $$ E = mc^2 $$
            """)

        if st.button("발행하기"):
            st.balloons()
            if st.button("새 글 작성하기"):
                return True
        return False
