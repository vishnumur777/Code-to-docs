from fastmcp import FastMCP
from dotenv import load_dotenv
import requests
import os
import ast

load_dotenv()

mcp = FastMCP("GitHub-Content")
os.environ["MCP_HTTP_HOST"] = "127.0.0.1"
os.environ["MCP_HTTP_PORT"] = "8002"

@mcp.tool()
def search_repo_github(repo: str, query: str) -> list:
    url = f"https://api.github.com/search/code"

    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3+json",
    }
    params = {
        "q": f"{query}+repo:{repo}",
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    items = response.json().get("items", [])
    
    results = []
    for item in items:
        results.append({
            "name": item["name"],
            "path": item["path"],
            "url": item["html_url"],
            "repository": item["repository"]["full_name"]
        })
    
    return results


@mcp.tool()
def get_file_content_github(repo: str, path: str) -> str:
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3.raw",
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.text

@mcp.tool()
def get_commit_history_github(repo: str, path: str) -> list:
    url = f"https://api.github.com/repos/{repo}/commits"
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3+json",
    }
    params = {
        "path": path,
        "per_page": 10
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    commits = response.json()
    history = []
    for commit in commits:
        history.append(commit["commit"]["message"])

    return history

@mcp.tool()
def get_readme_content_github(repo: str) -> str:
    url = f"https://api.github.com/repos/{repo}/readme"
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3.raw",
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.text

@mcp.tool()
def get_changelog_content_github(repo: str) -> str:
    possible_names = ["CHANGELOG.md", "Changelog.md", "changelog.md", "CHANGES.md", "Changes.md", "changes.md"]
    for name in possible_names:
        try:
            content = get_file_content_github(repo, name)
            return content
        except requests.HTTPError:
            continue
    return "No changelog file found."

@mcp.tool()
def get_contributing_content_github(repo: str) -> str:
    possible_names = ["CONTRIBUTING.md", "Contributing.md", "contributing.md"]
    for name in possible_names:
        try:
            content = get_file_content_github(repo, name)
            return content
        except requests.HTTPError:
            continue
    return "No contributing file found."

@mcp.tool()
def extract_docstrings(file_path):
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())
    return [ast.get_docstring(node) for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module))]

@mcp.tool()
def get_file_content_local(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read()



if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8002)