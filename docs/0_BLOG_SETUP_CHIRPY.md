### Chirpy 테마 블로그 설정 가이드

이 문서는 Chirpy 테마를 사용하여 GitHub Pages에 개인 블로그를 설정하는 방법을 단계별로 안내합니다. 이 가이드는 복잡한 설정 과정을 단순화하여 기술적인 지식이 많지 않은 사용자도 쉽게 따라 할 수 있도록 구성되었습니다.

### 1. 전제 조건

  * **GitHub 계정**: GitHub에 가입되어 있어야 합니다.
  * **Git 기본 지식**: 터미널(Terminal)에서 Git 명령어를 사용할 수 있어야 합니다.

### 2. 시작 가이드: Chirpy Starter 포크하기

가장 쉽고 권장되는 방법은 Chirpy Starter Repository를 사용하는 것입니다. 이 리포지토리는 불필요한 데모 콘텐츠를 포함하지 않아 링크 오류를 방지합니다.

1.  **Starter Repository 포크**:

      * `https://github.com/cotes2020/chirpy-starter.git ` 로 이동합니다.
      * 페이지 오른쪽 상단의 **'Fork'** 버튼을 클릭하여 본인의 계정으로 복사합니다.

2.  **리포지토리 이름 변경**:

      * 포크한 리포지토리로 이동합니다.
      * **Settings > General** 탭을 클릭합니다.
      * **Repository name** 섹션에서 이름을 `YourUsername.github.io` 형식으로 변경합니다. (예: `Wchoi189.github.io`).
      * **'Rename'** 을 클릭합니다. 이 작업을 완료하면 GitHub Pages 기능이 자동으로 활성화됩니다.

3.  **로컬에 클론**:

      * 터미널을 열고 다음 명령어를 실행하여 리포지토리를 로컬 컴퓨터로 복제합니다.

    <!-- end list -->

    ```
    git clone https://github.com/YourUsername/YourUsername.github.io.git
    cd YourUsername.github.io
    ```

### 3. 블로그 설정하기

이제 복제한 리포지토리의 설정을 변경합니다.

1.  **`_config.yml` 파일 수정**:

      * 텍스트 편집기(예: VS Code)로 `_config.yml` 파일을 엽니다.
      * 다음 필드를 본인의 정보로 업데이트합니다.

    <!-- end list -->

    ```yaml
    url: "https://YourUsername.github.io"
    title: "나의 블로그"
    tagline: "나의 태그라인"
    description: "블로그에 대한 간략한 설명"
    github:
      username: YourUsername
    social:
      name: 당신의 이름
      email: your.email@example.com
    ```

2.  **프로필 이미지 추가**:

      * `assets/images/avatar.jpg` 파일을 본인의 프로필 사진으로 교체합니다.

3.  **첫 번째 포스트 작성**:

      * `_posts` 폴더에 새 파일을 만듭니다. 파일 이름은 `YYYY-MM-DD-title.md` 형식으로 지정해야 합니다.
      * 예시: `2025-08-30-my-first-post.md`
      * 파일 상단에 다음 내용(YAML Front Matter)을 추가합니다.

    <!-- end list -->

    ```markdown
    ---
    title: 나의 첫 번째 포스트
    date: 2025-08-30
    categories: [Blog]
    ---

    # 안녕하세요!

    이것은 나의 첫 번째 블로그 포스트입니다.
    ```

### 4. 배포하기

모든 설정을 마친 후, GitHub에 변경 사항을 푸시하여 블로그를 배포합니다.

1.  **변경 사항 커밋 및 푸시**:

    ```bash
    git add .
    git commit -m "블로그 초기 설정 완료"
    git push origin main
    ```
2.  **GitHub Pages 확인**:
      * GitHub 리포지토리로 돌아가서 **Settings > Pages** 탭을 확인합니다.
      * `Source`가 **"Deploy from a branch"** 로, `Branch`가 **`main`** 으로 설정되어 있는지 확인합니다.
      * 잠시 후, "Your site is live at `https://YourUsername.github.io`" 라는 메시지와 함께 블로그 주소가 표시됩니다.

### 5. 문제 해결 (선택 사항)

  * **빌드 실패**: GitHub 리포지토리의 **Actions** 탭을 확인하여 빌드 오류를 검토합니다.
  * **로컬에서 미리 보기**: 블로그를 로컬 환경에서 테스트하려면 다음 명령어를 실행합니다.
  
    ```bash
    bundle install
    bundle exec jekyll serve
    ```
      * `http://localhost:4000` 에서 블로그를 미리 볼 수 있습니다.
