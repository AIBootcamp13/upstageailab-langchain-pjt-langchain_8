# 03_CONTEXT_LOG.md: Project Summary

Of course. Here is a summary of the changes to update your context log, including the switch to `PyMuPDF`.

---
## **Updated Context Log Summary**

**Date**: August 26, 2025

### **Project Update: Architectural Shift to Local-First RAG Processing**

This update details the project's architectural evolution from an API-dependent workflow to a fully self-contained, local-first RAG pipeline. The primary motivation for this change was to resolve a critical dependency conflict and gain full control over the data processing workflow.

* **Problem Identification**: The initial architecture, which used `langchain-upstage` to connect to the Upstage API for PDF parsing, created a dependency conflict. The client library required an older version of the `pypdf` package that was incompatible with other key libraries in the project, such as `llama-index`.

* **Architectural Solution**: To resolve this, the project has pivoted to a self-contained architecture that handles all data processing locally without relying on external APIs for its core pipeline.
    * **PDF Parsing**: The `UpstageDocumentParseLoader` has been replaced with a local, library-based solution. [cite_start]After analysis, **`PyMuPDF` was chosen** for its superior performance and excellent handling of Korean character encoding, ensuring high-quality text extraction directly within the environment. [cite: 229, 235]
    * [cite_start]**Embedding**: The system now uses open-source `HuggingFaceEmbeddings` (e.g., `bge-base-en-v1.5` or `bge-m3`) instead of relying on the OpenAI API, bringing the embedding process in-house. [cite: 21, 25, 52]
    * [cite_start]**LLM Execution**: The project continues to leverage **Ollama** for running powerful open-source LLMs locally, ensuring data privacy and cost efficiency. [cite: 6, 17]

This strategic shift successfully resolves the dependency issues, eliminates external API costs for parsing, and provides greater control and stability over the entire RAG pipeline.

----
**Date:** August 26, 2025

### **Consolidated Project Summary**

**Project Title:** Advanced RAG & Agentic AI Systems

**Overall Objective:** To build and operationalize a series of advanced Retrieval-Augmented Generation (RAG) and Agentic AI systems. The project encompasses refactoring existing codebases, building a foundational hybrid RAG pipeline, and culminating in the development of an autonomous "PPT-to-Blog" agent that can generate and deploy content.

**Core Technologies:**
* **LLMs:** Local models via **Ollama** (e.g., 13B-20B models), API models via **OpenAI** (GPT series), Hugging Face models (`transformers`).
* **Frameworks:** **LangChain** (for chaining, agents, LCEL), **LlamaIndex** (for data ingestion and RAG), **LangGraph** (for stateful, multi-step agents).
* **Vector Store:** **ChromaDB** (local), **FAISS**.
* **Tools & APIs:** **Tavily** (Web Search), **GitHub API**.
* **Development:** Python, `dotenv` for configuration, `pytest` for testing, Streamlit for UI.

---

### **Phase 1: Foundational Work (Completed)**

This phase focused on building the core RAG pipeline and modernizing all existing scripts to ensure compatibility and best practices.

**1.1. Core RAG Pipeline Implementation:**
A fully functional hybrid RAG pipeline has been built to generate blog posts from PDF documents and web search results.
* **Ingestion (`src/ingestion.py`):** Loads and chunks PDF documents from `data/source_pdfs/`.
* **Indexing (`src/indexing.py`):** Embeds document chunks and stores them in a ChromaDB vector store.
* **Generation (`src/generation.py`):** Implements a hybrid RAG chain that uses both the local vector store and Tavily web search results to generate high-quality content using an LLM served via Ollama.
* **Execution (`src/main.py`):** A main script orchestrates the entire pipeline via command-line input.

**1.2. Codebase Refactoring & Modernization:**
All provided scripts were refactored to work with the latest versions of major libraries.
* **OpenAI & LlamaIndex Scripts:** Updated to use modern clients (`openai v1.x`), new modular import structures (`llama_index.core`), and the `Settings` object for configuration.
* **Local LLM Scripts:** Corrected local model loading (`AutoModelForCausalLM`) and standardized path management.
* **Fine-tuning & Agent Scripts:** Verified compatibility for `transformers`, `peft`, `trl`, and updated all `langchain` imports to the new `langchain_core`/`_community`/`_openai` structure, ensuring proper use of LangChain Expression Language (LCEL) and LangGraph's stateful agent architecture.

---

### **Phase 2: "PPT-to-Blog" Agent with GitHub Deployment (In Progress)**

This phase focuses on extending the core pipeline by implementing an agent that can automatically generate a blog post from a PowerPoint file and publish it to a GitHub Pages blog.

**2.1. Goal:**
To create an end-to-end workflow where a user provides a `.pptx` file and, with an optional flag (`--publish`), the system generates a Markdown blog post and commits it to a specified GitHub repository.

**2.2. Current State & Existing Assets:**
* **Hardware:** The user's **RTX 3090 (24GB)** is confirmed suitable for hosting the required local Ollama models.
* **GitHub Tool (`scripts/tools.py`):** A pre-built LangChain tool, `post_to_github_blog`, already exists for publishing content via the GitHub API.
* **Agent Example (`scripts/agent_script.py`):** A complete example of a LangChain agent using the `post_to_github_blog` tool is available.
* **Integration Gap:** The main application (`src/main.py`) can generate content but lacks the logic to invoke the publishing agent. Configuration for the GitHub tool is not yet centralized.

**2.3. Implementation Plan & Checklist:**

**Step 1: Centralize Configuration**
* [X] **Update `.env`:** Add `GITHUB_PAT`, `GITHUB_REPO_OWNer="Wchoi189"`, and `GITHUB_REPO_NAME="Wchoi189.github.io"`.
* [ ] **Update `src/config.py`:** Add logic to load the new GitHub environment variables.
* [ ] **Refactor `scripts/tools.py`:** Modify the `post_to_github_blog` tool to use the centralized configuration variables instead of placeholders.

**Step 2: Integrate Agent into Main Workflow**
* [ ] **Modify `src/main.py`:** Add a `--publish` command-line argument.
* [ ] **Implement Agent Logic:** If the `--publish` flag is used, `src/main.py` will:
    * Instantiate the agent and the `post_to_github_blog` tool (re-using logic from `scripts/agent_script.py`).
    * Invoke the agent with the generated blog title and content.
    * Print the agent's result (e.g., success URL) to the console.

**Step 3: Update Documentation**
* [ ] **Update `docs/02_USAGE_GUIDE.md` & `README.md`:**
    * Add instructions for creating a GitHub Personal Access Token.
    * Update the `.env` example with the new variables.
    * Update command-line examples to show the new `--publish` flag.
    * Add the publishing feature to the list of implemented features.

---

### **Phase 3: Future Work & Enhancements (To-Do)**

Once the GitHub publishing agent is fully integrated, the following tasks are planned to improve the project's usability, stability, and quality.

* **[ ] UI Development (`src/ui/`):** Develop a Streamlit web interface for user-friendly interaction.
* **[ ] Testing (`tests/`):** Write unit and integration tests using `pytest` to ensure code stability and reliability.
* **[ ] Model & Prompt Engineering:** Experiment with different LLMs (e.g., Upstage Solar, GPT-4o-mini) and continuously refine prompt templates to improve the quality of generated content.
* **[ ] Advanced Documentation:** Enhance in-code docstrings and add comprehensive architecture documents in the `docs/` directory.

  _This log will track the progress of the implementations planned for the project._