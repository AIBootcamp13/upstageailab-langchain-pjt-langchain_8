# Your blog generation script
from langchain_community.chat_models import ChatOllama  # Using Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


llm = ChatOllama(model="phi3:14b-medium-128k-instruct")

# This prompt is the "brain" of your content generator
blog_prompt_template = """
You are an expert tech blogger. Your task is to write a clear, engaging, and well-structured blog post in Markdown format based on the provided context from a presentation.

[CONTEXT FROM PRESENTATION]
---
{context}
---

[INSTRUCTIONS]
1.  Create a compelling and SEO-friendly title (H1).
2.  Write a brief introduction that hooks the reader and summarizes the topic.
3.  Organize the main content into logical sections with clear headings (H2 or H3).
4.  Use bullet points, code blocks, and bold text to improve readability.
5.  Write a concluding paragraph that summarizes the key takeaways.
6.  The tone should be informative and accessible to a technical audience.

[BLOG POST OUTPUT]
"""
prompt = ChatPromptTemplate.from_template(blog_prompt_template)
blog_generation_chain = prompt | llm | StrOutputParser()

# --- To run it ---
# 1. Read the PPT file into a single string:
#    from llama_index.core import SimpleDirectoryReader
#    docs = SimpleDirectoryReader(input_dir="./ppt_data").load_data()
#    ppt_content = "\\n\\n".join([doc.page_content for doc in docs])
#
# 2. Invoke the chain:
#    markdown_blog_post = blog_generation_chain.invoke({"context": ppt_content})
#    print(markdown_blog_post)
