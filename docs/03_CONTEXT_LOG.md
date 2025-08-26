# 03_CONTEXT_LOG.md: Project Summary

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