# tools.py
import base64
import os
from datetime import datetime

import requests
from langchain.tools import tool


# HTTP status code for resource creation
CREATED_STATUS_CODE = 201


@tool
def post_to_github_blog(title: str, content: str) -> str:
    """
    Publishes a blog post to a GitHub Pages repository by creating a new markdown file
    in the '_posts' directory via the GitHub API. The title is used to generate the filename.
    """
    github_token = os.getenv("GITHUB_PAT")
    repo_owner = "your-github-username"
    repo_name = "your-github-repo-name"

    # Format the filename as YYYY-MM-DD-title.md
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = title.lower().replace(" ", "-").strip()
    file_name = f"{date_str}-{slug}.md"

    # Prepare the file content for the API (must be base64 encoded)
    # Add Jekyll front matter
    full_content = f'---\ntitle: "{title}"\nlayout: post\n---\n\n{content}'
    encoded_content = base64.b64encode(full_content.encode("utf-8")).decode("utf-8")

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/_posts/{file_name}"

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    data = {
        "message": f"New blog post: {title}",
        "content": encoded_content,
        "branch": "main",  # or "master"
    }

    response = requests.put(url, headers=headers, json=data, timeout=10)

    if response.status_code == CREATED_STATUS_CODE:
        return f"Successfully created post at {response.json()['content']['html_url']}"
    return f"Failed to create post. Status: {response.status_code}, Info: {response.text}"
