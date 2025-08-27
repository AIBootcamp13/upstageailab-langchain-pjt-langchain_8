# **프로젝트 설정 (config.yaml) 사용 가이드 (Poetry)**

이 문서는 `config.yaml` 파일을 사용하여 프로젝트의 모든 설정을 관리하는 방법을 안내합니다. 이 파일을 통해 실행 환경, 데이터 처리 방식, 검색 옵션을 손쉽게 변경할 수 있습니다.

### **시작하기 전에: 의존성 설치**

이 프로젝트는 `Poetry`를 사용하여 패키지를 관리합니다. 프로젝트를 처음 설정하거나 새로운 동료가 참여할 때, 필요한 모든 라이브러리는 `pyproject.toml` 파일에 이미 정의되어 있습니다.

따라서, 아래 명령어 단 하나만 실행하여 모든 의존성을 한 번에 설치하세요.

```bash
poetry install
```

**참고**: `poetry add <package_name>` 명령어는 프로젝트에 **새로운** 라이브러리를 추가할 때만 사용합니다.

#### **macOS 사용자 참고: pysqlite3-binary 설치 문제**

이 프로젝트가 사용하는 벡터 저장소(chromadb)는 최신 버전의 SQLite 데이터베이스를 필요로 하며, 이를 위해 pysqlite3-binary 패키지에 의존합니다. 하지만 이 패키지는 일부 macOS 환경(특히 Apple Silicon/ARM 아키텍처)에서 호환성 문제를 일으킬 수 있습니다.

**해결 방법**: `poetry install` 실행 중 오류가 발생하면, 아래와 같이 환경 변수를 설정하여 SQLite를 소스 코드로부터 직접 컴파일하도록 강제한 후 다시 설치를 시도하세요.

```bash
GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=1 GRPC_PYTHON_BUILD_SYSTEM_ZLIB=1 poetry install
```

### **1. 실행 환경 설정 (환경 프로필) ⚙️**

프로젝트는 사용자의 하드웨어 환경(CPU/GPU)에 맞춰 최적의 모델을 선택할 수 있도록 **프로필 기반 설정**을 지원합니다. 터미널에서 `ENV_PROFILE` 환경 변수를 설정하여 원하는 프로필을 활성화할 수 있습니다.  
예시:

- **Linux / macOS**  
    ```bash
    ENV_PROFILE=high_gpu poetry run python main.py
    ```

- **Windows (PowerShell)**  
    ```powershell
    $env:ENV_PROFILE="high_gpu"; poetry run python main.py
    ```

* **default_cpu**: 고성능 GPU가 없는 환경을 위한 기본 프로필입니다. **OpenAI API**를 사용하여 모델을 실행하므로, API 키가 필요하며 비용이 발생할 수 있습니다.  
* **high_gpu**: 강력한 로컬 GPU가 있는 환경을 위한 프로필입니다. **HuggingFace**와 **Ollama**를 통해 오픈소스 모델을 로컬에서 직접 실행하므로 비용이 발생하지 않습니다.

#### **프로필 선택 방법**

Poetry 환경에서는 `poetry run` 명령어 앞에 환경 변수를 지정하여 실행합니다.

* **Linux / macOS**  
  ```bash
  ENV_PROFILE=high_gpu poetry run python main.py
  ```

* **Windows (PowerShell)**  
  ```powershell
  $env:ENV_PROFILE="high_gpu"; poetry run python main.py
  ```

#### **💡 Ollama 로컬 모델 실행 방법 (high_gpu 프로필 사용 시)**

high_gpu 프로필을 사용하려면 먼저 Ollama 서버를 실행하고 원하는 모델을 다운로드해야 합니다.

1. Ollama 서버 실행:  
   새로운 터미널을 열고 아래 명령어를 입력하여 Ollama 서버를 시작합니다. 서버가 실행 중인 동안 이 터미널은 계속 열어두어야 합니다.  
   ```bash
   ollama serve
   ```

2. 모델 다운로드:  
   다른 터미널을 열고 `config.yaml`에 지정된 `gpt-oss:20b` 모델을 다운로드합니다.  
   ```bash
   ollama pull gpt-oss:20b
   ```

3. 모델 실행 확인 (선택 사항):  
   아래 명령어로 모델이 정상적으로 실행되는지 테스트할 수 있습니다.  
   ```bash
   ollama run gpt-oss:20b
   ```

   이제 프로젝트에서 high_gpu 프로필을 선택하면 로컬 모델을 사용할 준비가 완료됩니다.

#### **💡 export 명령어는 언제 사용하나요?**

`export` 명령어는 현재 터미널 세션 전체에 환경 변수를 설정할 때 사용합니다. 한번 설정해두면, 터미널을 닫기 전까지는 매번 명령어를 입력할 때마다 `ENV_PROFILE`을 다시 지정할 필요가 없습니다.

* **세션 전체에 프로필 고정하기:**  
  ```bash
  export ENV_PROFILE=high_gpu
  ```

  이제부터는 간단하게 `poetry run python main.py`만 실행하면 됩니다.  
* 일회성으로 프로필 지정하기:  
  위의 예시처럼 `ENV_PROFILE=high_gpu poetry run ...` 형식으로 사용하면 해당 명령어에만 환경 변수가 적용됩니다. 여러 프로필을 번갈아 테스트할 때 유용합니다.

### **2. 데이터 수집 설정 (ingestion) 📄**

이 섹션은 PDF 문서를 데이터베이스에 저장하기 전, 어떻게 처리할지를 결정합니다.

#### **PDF 파서 선택 (parser)**

`config.yaml` 파일에서 `parser` 값을 변경하여 PDF 텍스트 추출 방식을 선택합니다.

```yaml
# --- 데이터 수집 (Ingestion) 설정 ---  
ingestion:  
  # PDF 파서(parser) 선택: "local", "api", "unstructured" 중 하나를 선택  
  parser: "local"
```

* **parser: "local"**: PyMuPDF를 사용한 빠르고 가벼운 로컬 파서.  
* **parser: "api"**: Upstage Layout Analysis API를 사용. (API 키 필요)  
* **parser: "unstructured"**: unstructured.io를 사용한 강력한 로컬 파서.

#### **텍스트 분할 (text_splitter)**

추출된 텍스트를 검색에 용이하도록 작은 단위(chunk)로 자르는 방식을 설정합니다.

```yaml
  # Text Splitter Settings ---  
  text_splitter:  
    chunk_size: 1024      # 텍스트를 나눌 최대 크기  
    chunk_overlap: 256    # 나눠진 조각들이 겹칠 내용의 크기
```

### **3. 벡터 저장소 설정 (vector_store) 🔍**

이 섹션은 사용자의 질문과 가장 관련 높은 문서 조각을 어떻게 찾아올지(retrieval)를 설정합니다.

#### **검색 타입 (search_type)**

`search_type` 값을 변경하여 검색 알고리즘을 선택합니다.

```yaml
# --- 벡터 저장소 (Vector Store) 설정 ---  
vector_store:  
  collection_name: "lecture_documents"  
  # 검색 타입: "mmr" 또는 "similarity"  
  search_type: "mmr"
```

* **search_type: "similarity"**: 질문과 의미적으로 가장 **유사한** 내용만 찾습니다.  
* **search_type: "mmr"**: **유사성**과 **다양성**을 함께 고려하는 고급 방식입니다. (권장)

#### **검색 인자 (search_kwargs)**

`k` 값을 조절하여 검색 결과의 수를 결정합니다.

```yaml
  # 검색 관련 인자 (k: 반환할 문서 수)  
  search_kwargs:  
    k: 5
```

* k: 질문에 대한 답변의 근거로 삼기 위해 데이터베이스에서 **가져올 문서 조각의 수**를 결정합니다.