# README.md

# 프로젝트 설정 안내

이 문서는 프로젝트 실행에 필요한 외부 라이브러리 설치 방법을 안내합니다.

---

## ## 필수 설치 라이브러리

이 프로젝트는 PDF 문서를 처리하기 위해 외부 라이브러리를 사용하며, 특히 고급 파싱(parsing) 전략을 사용할 때 반드시 필요합니다.

### ### Poppler 🖼️
**Poppler**는 PDF 렌더링 라이브러리입니다. `"hi_res"` 파싱 전략을 사용할 때 PDF 페이지를 이미지로 변환하여 분석하기 위해 필요합니다.

**설치 방법 (Debian/Ubuntu):**
```bash
sudo apt-get update && sudo apt-get install -y poppler-utils
````
-----

### ### Tesseract OCR 📖

**Tesseract**는 광학 문자 인식(OCR) 엔진입니다. `"hi_res"` 및 `"ocr_only"` 전략에서 이미지나 스캔된 문서로부터 텍스트를 추출하는 데 사용됩니다. 아래 명령어에는 한국어 언어팩(`tesseract-ocr-kor`)이 포함되어 있습니다.

**설치 방법 (Debian/Ubuntu):**

```bash
sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-kor
```


---

# Debug streamlit
pkill -f 'streamlit run' || true; sleep 1; poetry run streamlit run src/app.py --logger.level=debug

# Debug and output log file
pkill -f 'streamlit run' || true; sleep 1; poetry run streamlit run src/app.py --logger.level=debug > /tmp/streamlit.log 2>&1 & echo $! > /tmp/streamlit.pid; sleep 2; tail -n 200 /tmp/streamlit.log

---

You've asked a great question! It's a sharp observation.

No, the logic was not removed from the `generate_draft` method. It was intentionally **refactored** for better code organization.

Here's a breakdown of what changed:

* **Before**: The `chain` used for generating the draft was created inside the `generate_draft` method every time it was called.
* **Now**: The chain is created just once as `self.draft_chain` when the `BlogContentAgent` is first initialized in the `__init__` method. The `generate_draft` method now simply uses this pre-built chain.

This is a common and good practice because it makes the code more efficient by not rebuilding the chain on every call.

The core logic, `self.retriever | self.format_docs`, which retrieves documents and formats them before sending them to the language model, is still intact and works exactly as it did before.


----