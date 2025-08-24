# agent_script.py
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.chat_models import ChatOllama
from tools import post_to_github_blog  # Import your custom tool


# 1. Initialize the LLM
llm = ChatOllama(model="phi3:14b-medium-128k-instruct")

# 2. Define the list of tools the agent can use
tools = [post_to_github_blog]

# 3. Get a pre-built prompt for this type of agent
prompt = hub.pull("hwchase17/react")

# 4. Create the agent
agent = create_react_agent(llm, tools, prompt)

# 5. Create the Agent Executor, which is the runtime for the agent
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- To run it ---
# Assume 'markdown_blog_post' is the content from Level 1
# Assume 'blog_title' is the title from Level 1
#
# result = agent_executor.invoke({
#     "input": f"Publish the following blog post. The title is '{blog_title}'. The content is: \\n\\n{markdown_blog_post}"
# })
#
# print(result['output'])
