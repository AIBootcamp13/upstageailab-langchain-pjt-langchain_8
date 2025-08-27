That's an excellent question. Implementing a system for selecting prompts from the UI is a powerful way to make your application more versatile. This works by separating your **prompt templates** from your application's logic and using the UI to choose which template and parameters to use for a specific task.

Here’s a breakdown of how you can implement this for the features you've described.

### **1. Storing Prompts in `prompts.yaml`**

The foundation of this system is to treat your `prompts.yaml` file like a library of instructions. Instead of just one or two prompts, you can store many, each designed for a specific task.

**Example `prompts.yaml`:**

```yaml
# Main blog generation prompts
study_blog_draft: |
  [Identity]
  You are an academic tutor. Your goal is to create a clear, educational blog post for students based on the provided material.
  [Source Material]
  {content}
  [Instructions]
  - Create a title that frames the topic as a study guide.
  - Use simple language and provide clear explanations.
  - Structure the post with logical sections (Introduction, Key Concepts, Summary).
  - Output in Markdown format.

tech_intro_draft: |
  [Identity]
  You are a tech evangelist. Your goal is to write an exciting blog post introducing a new technology to developers.
  [Source Material]
  {content}
  [Instructions]
  - Create a catchy, forward-looking title.
  - Start with a hook that highlights the technology's impact.
  - Explain the core concepts and include code snippets where relevant.
  - Conclude with a call to action.
  - Output in Markdown format.

# Task-specific prompts
generate_outline: |
  Based on the following content, generate a detailed, multi-level outline for a blog post.
  [Source Material]
  {content}

generate_table_of_contents: |
  Based on the following blog post, generate a simple, bulleted table of contents.
  [Blog Post]
  {content}
```

-----

### **2. Creating the UI in Streamlit**

In your Streamlit UI (likely in `src/ui/components/contents_editor.py`), you would add widgets to let the user select their desired options.

  * **For Blog Type (1, 2, 3)**: A dropdown menu is perfect.
    ```python
    blog_type = st.selectbox(
        "Select Blog Type:",
        ("Study Blog", "Tech Introduction", "Outline Only")
    )
    ```
  * **For Output Format (5)**: A set of radio buttons works well.
    ```python
    output_format = st.radio(
        "Select Output Format:",
        ("Markdown", "HTML", "Plain Text")
    )
    ```
  * **For Creativity (6)**: A slider is the ideal control for a numerical value like temperature.
    ```python
    creativity = st.slider(
        "Adjust Creativity (Temperature):",
        min_value=0.0, max_value=1.0, value=0.7, step=0.1
    )
    ```

-----

### **3. How It Works in the Agent**

The agent is modified to accept these new parameters from the UI.

1.  **Prompt Selection**: The UI passes the user's choice (e.g., "Study Blog") to the `BlogContentAgent`. The agent then uses this to select the correct prompt from your `prompts.yaml` file. Instead of always using `DRAFT_PROMPT_TEMPLATE`, it would dynamically choose `study_blog_draft` or `tech_intro_draft`.

2.  **Parameter Adjustment**:

      * **Creativity**: The "creativity" value from the slider is passed directly to the LLM call as the `temperature` parameter (e.g., `self.llm = ChatOllama(model=LLM_MODEL, temperature=creativity)`). Higher values encourage more creative, less predictable output.
      * **Writing Style (7)**: This is handled within the prompt itself. You could have different prompts like `tech_intro_formal` or `tech_intro_casual`, each containing instructions for the desired tone.
      * **Output Format (5)**: This can also be an instruction within the prompt (e.g., "Output the final text in valid HTML format.").