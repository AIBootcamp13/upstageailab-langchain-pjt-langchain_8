# GitHub Pages 블로그 생성 가이드

GitHub Pages를 사용하여 Jekyll 블로그를 설정하고 스크립트에서 포스트를 받을 수 있도록 저장소를 구성하는 방법을 안내합니다.

가장 간단한 설정을 위해서는 저장소 이름을 `<github_username>.github.io`**로 **설정하는 것을 권장**합니다. 이 특별한 명명 규칙을 사용하면 GitHub에서 개인 사용자 사이트로 인식하여 `https://<github_username>.github.io`에서 사이트가 활성화됩니다.

---

## 📝 설정 계획

빈 저장소를 Jekyll 블로그로 구성하려면 다음 단계를 따르세요.

### **1단계: 테마 선택 및 `_config.yml` 생성**

가장 쉬운 시작 방법입니다. GitHub에서 메인 구성 파일을 자동으로 생성해줍니다.

1. 저장소에서 **Settings** 탭으로 이동합니다.
2. 왼쪽 사이드바에서 **Pages**를 클릭합니다.
3. "Build and deployment" 섹션에서 "Theme Chooser"를 찾아 **Choose a theme**를 클릭합니다.
4. 원하는 테마(예: Minimal)를 선택하고 **Select theme**를 클릭합니다.
5. 이렇게 하면 저장소에 `_config.yml` 파일이 생성됩니다. 이 파일을 편집하여 제목과 설명을 추가할 수 있습니다.
   ```yaml
   # _config.yml
   title: My AI-Generated Blog
   description: RAG 애플리케이션으로 생성된 포스트
   theme: jekyll-theme-minimal
   ```

### **2단계: 블로그 포스트 디렉토리 생성**

Python 스크립트는 `_posts` 디렉토리에 글을 게시하도록 설계되어 있습니다. 이 폴더를 생성해야 합니다.

1. 저장소 메인 페이지에서 **Add file** > **Create new file**을 클릭합니다.
2. 파일명 입력란에 `_posts/`를 입력한 후 `.gitkeep`을 입력합니다.
3. 이렇게 하면 빈 `_posts` 디렉토리가 생성되고 폴더가 저장소에 존재하도록 보장하는 숨김 파일이 포함됩니다. **Commit changes**를 클릭합니다.

### **3단계: 레이아웃 템플릿 생성**

Jekyll은 레이아웃 파일을 사용하여 콘텐츠를 렌더링합니다. 스크립트는 특히 `post` 레이아웃을 사용하는 포스트를 생성합니다.

1. **`_layouts` 폴더 생성:** **Add file** > **Create new file**을 클릭하고 `_layouts/default.html`로 이름을 지정합니다.
2. **기본 default 레이아웃을 위한 다음 코드를 붙여넣고** 파일을 커밋합니다.
   ```html
   <!DOCTYPE html>
   <html>
     <head>
       <title>{{ page.title }}</title>
     </head>
     <body>
       {{ content }}
     </body>
   </html>
   ```
3. **`post` 레이아웃 생성:** **Add file** > **Create new file**을 다시 클릭하고 `_layouts/post.html`로 이름을 지정합니다.
4. **간단한 블로그 포스트 레이아웃을 위한 다음 코드를 붙여넣고** 파일을 커밋합니다.
   ```html
   ---
   layout: default
   ---
   <h1>{{ page.title }}</h1>
   <p>{{ page.date | date_to_string }}</p>
   <hr>
   {{ content }}
   ```

### **4단계: 홈페이지 생성**

마지막으로 향후 블로그 포스트를 나열할 간단한 홈페이지를 생성합니다.

1. 저장소 메인 페이지에서 **Add file** > **Create new file**을 클릭합니다.
2. 파일명을 `index.md`로 지정합니다.
3. `_posts` 폴더의 모든 포스트를 자동으로 나열하는 다음 내용을 붙여넣습니다.
   ```markdown
   ---
   layout: default
   ---
   # 내 블로그에 오신 것을 환영합니다

   ## 포스트
   <ul>
     {% for post in site.posts %}
       <li>
         <a href="{{ post.url }}">{{ post.title }}</a>
       </li>
     {% endfor %}
   </ul>
   ```
4. **Commit changes**를 클릭합니다.

이 파일들을 커밋한 후 GitHub에서 자동으로 Jekyll 사이트를 빌드합니다. 몇 분 내에 **`https://<github_username>.github.io`**에서 블로그가 활성화되어 RAG 애플리케이션에서 포스트를 받을 수 있도록 완전히 구성됩니다.

---

## 'Theme Chooser'를 사용할 수 없는 경우

GitHub의 인터페이스는 다양할 수 있습니다. "Classic Pages Experience"에서는 더 수동적인 설정이 필요하지만 똑같이 간단합니다.

주요 차이점은 테마 선택기가 대신 해주는 것이 아니라 직접 `_config.yml` 파일을 생성한다는 것입니다.

### 📝 수정된 설정 계획 (Classic Experience)

### **1단계: `_config.yml` 파일 수동 생성**

고 어떤 테마를 사용할지 알려줍니다.

1. 저장소 메인 페이지에서 **Add file** > **Create new file**을 클릭합니다.

2. 파일명을 `_config.yml`로 지정합니다.

3. 다음 구성을 파일에 붙여넣습니다. 이는 깔끔하고 미니멀한 테마를 설정합니다.

   ```yaml
   # _config.yml
   title: My AI-Generated Blog
   description: RAG 애플리케이션으로 생성된 포스트
   theme: jekyll-theme-minimal
   ```

4. **Commit changes**를 클릭합니다.

### **2단계: 블로그 디렉토리 및 레이아웃 생성**

이 단계들은 이전과 동일합니다. 블로그 포스트를 위한 폴더와 템플릿 파일을 생성해야 합니다.

1. **`_posts` 디렉토리 생성**:
   * **Add file** > **Create new file**을 클릭합니다.
   * `_posts/.gitkeep`로 이름을 지정하고 커밋합니다. 이렇게 하면 빈 디렉토리가 생성됩니다.

2. **`_layouts` 및 템플릿 생성**:
   * `_layouts/default.html`이라는 파일을 생성하고 아래 코드를 붙여넣습니다:
     ```html
     <!DOCTYPE html>
     <html>
       <head>
         <title>{{ page.title }}</title>
       </head>
       <body>
         {{ content }}
       </body>
     </html>
     ```
   * `_layouts/post.html`이라는 파일을 생성하고 아래 코드를 붙여넣습니다:
     ```html
     ---
     layout: default
     ---
     <h1>{{ page.title }}</h1>
     <p>{{ page.date | date_to_string }}</p>
     <hr>
     {{ content }}
     ```

### **3단계: 홈페이지 생성**

포스트를 나열할 `index.md` 파일을 생성합니다.

1. `index.md`라는 파일을 생성합니다.
2. 다음 내용을 붙여넣습니다:
   ```markdown
   ---
   layout: default
   ---
   # 내 블로그에 오신 것을 환영합니다

   ## 포스트
   <ul>
     {% for post in site.posts %}
       <li>
         <a href="{{ post.url }}">{{ post.title }}</a>
       </li>
     {% endfor %}
   </ul>
   ```

### **4단계: 게시 소스 확인**

마지막으로 **Settings > Pages**로 돌아갑니다. "Build and deployment" 섹션에서 **Source**가 **Deploy from a branch**로 설정되어 있고 브랜치가 **`main`**으로, 폴더가 **/ (root)**로 설정되어 있는지 확인합니다.

이 모든 파일을 커밋한 후 GitHub에서 사이트를 빌드합니다. 몇 분 후에 `https://<github_username>.github.io`에서 블로그가 활성화됩니다.

---

## 💡 추가 팁

- **포스트 파일명 형식**: `_posts` 디렉토리의 포스트는 `YYYY-MM-DD-제목.md` 형식으로 명명해야 합니다.
- **Front Matter**: 모든 포스트는 YAML front matter로 시작해야 합니다:
  ```yaml
  ---
  layout: post
  title: "포스트 제목"
  date: 2024-01-01
  ---
  ```
- **빌드 시간**: GitHub Pages는 변경사항을 반영하는 데 몇 분이 걸릴 수 있습니다.
- **사용자 정의**: `_config.yml`에서 더 많은 설정을 추가하여 블로그를 사용자 정의할 수 있습니다.
