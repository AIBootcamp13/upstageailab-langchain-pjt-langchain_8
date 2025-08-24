from urllib.parse import quote
# scripts/tools.py
import base64
from datetime import datetime

import requests
from langchain.tools import tool

from src import config

CREATED_STATUS_CODE = 201

@tool
def post_to_github_blog(title: str, content: str) -> str:
    """
    Publishes a blog post to a GitHub Pages repository by creating a new markdown file
    in the '_posts' directory via the GitHub API. The title is used to generate the filename.
    """
    github_token = config.GITHUB_PAT
    repo_owner = config.GITHUB_REPO_OWNER
    repo_name = config.GITHUB_REPO_NAME

    date_str = datetime.now().strftime("%Y-%m-%d")
    import re
    # Replace spaces with hyphens, remove colons and other unsafe characters
    slug = title.lower().replace(' ', '-')
    slug = re.sub(r'[^\w\-가-힣]', '', slug)
    slug = re.sub(r'-+', '-', slug)  # Replace multiple hyphens with a single hyphen
    slug = slug.strip('-')
    file_name = f"{date_str}-{slug}.md"

    full_content = (
        f"---\n"
        f"title: \"{title}\"\n"
        f"layout: post\n"
        f"date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S +0900')}\n"
        f"---\n\n"
        f"{content}"
    )
    encoded_content = base64.b64encode(full_content.encode("utf-8")).decode("utf-8")

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/_posts/{file_name}"

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    data = {
        "message": f"New blog post: {title}",
        "content": encoded_content,
        "branch": "main",
    }

    response = requests.put(url, headers=headers, json=data, timeout=10)

    if response.status_code == CREATED_STATUS_CODE:
        # Construct the public Jekyll URL instead of using the API response URL
        year, month, day = date_str.split('-')
        encoded_slug = quote(slug)
        public_url = f"https://{repo_owner}.github.io/{year}/{month}/{day}/{encoded_slug}.html"
        return f"Successfully created post. View it at: {public_url}"
        
    return f"Failed to create post. Status: {response.status_code}, Info: {response.text}"