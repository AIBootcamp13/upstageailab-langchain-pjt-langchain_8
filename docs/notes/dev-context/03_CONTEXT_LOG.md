# 03_CONTEXT_LOG.md: Project Summary

### **Project Context Log: Current State**

**Date**: August 27, 2025

**Project Title**: Configurable RAG Blog Generation System

**Overall Objective**: To build a flexible, production-ready RAG (Retrieval-Augmented Generation) system that can generate blog posts from PDF documents. The system is designed to be highly configurable, supporting different hardware environments and data processing strategies through a centralized configuration.

**Core Technologies**:
* **Frameworks**: **LangChain** (for core orchestration), **Streamlit** (for the user interface).
* **PDF Parsers**: Supports multiple, selectable parsers including **Upstage API**, **PyMuPDF** (local), and **Unstructured.io** (local, with OCR).
* **LLMs & Embeddings**: Supports both **API-based models** (OpenAI) for CPU environments and **local open-source models** (Ollama, HuggingFace) for GPU-accelerated environments.
* **Vector Store**: **ChromaDB**.
* **Configuration**: All settings are managed centrally in `configs/config.yaml` and `prompts/prompts.yaml`.

---
### **Architectural State: Fully Refactored & Configurable**

The project has successfully completed a major refactoring phase, achieving the following key architectural goals:

1.  **Centralized Configuration**: All hardcoded values have been removed from the source code. Application behavior, including model selection, parser choice, and prompt templates, is now controlled entirely by the `configs/config.yaml` and `prompts/prompts.yaml` files.

2.  **Configurable PDF Parsing**: The `DocumentPreprocessor` is now a flexible factory that can use one of three different PDF parsing strategies based on the `ingestion.parser` setting in the config file:
    * `"api"`: Uses the high-quality, layout-aware Upstage API.
    * `"local"`: Uses the fast and efficient `PyMuPDF` library.
    * `"unstructured"`: Uses the powerful `Unstructured.io` library with OCR capabilities for complex or scanned documents.

3.  **Dual Environment Profiles**: The system now supports two distinct hardware environments, selectable via the `ENV_PROFILE` environment variable:
    * **`default_cpu`**: For machines without a high-performance GPU, this profile uses API-based services like OpenAI for embeddings and LLM generation.
    * **`high_gpu`**: For machines with a powerful GPU, this profile uses local, open-source models via Ollama and HuggingFace, ensuring data privacy and cost-free operation.

This refactoring has transformed the project into a robust and maintainable application, ready for further development and experimentation.
  _This log will track the progress of the implementations planned for the project._