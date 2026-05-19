from mcp.server.fastmcp import FastMCP
import httpx
import os
import json
from google import genai
from google.genai import types
from typing import Dict, List, Any
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP("GitHubDevCard")

# Initialize Gemini Client
def get_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    return genai.Client(api_key=api_key)

@mcp.tool()
async def scrape_github(username: str) -> Dict[str, Any]:
    """Fetch GitHub stats and top repos for a given username."""
    async with httpx.AsyncClient() as client:
        # User profile
        user_res = await client.get(f"https://api.github.com/users/{username}")
        if user_res.status_code != 200:
            return {"error": f"User {username} not found"}
        user_data = user_res.json()

        # Repositories
        repos_res = await client.get(f"https://api.github.com/users/{username}/repos?sort=stars&per_page=30")
        repos_data = repos_res.json()

        top_repos = []
        languages = {}
        for repo in repos_data[:10]: # Look at top 10 for language stats
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
            
            if len(top_repos) < 6:
                top_repos.append({
                    "name": repo["name"],
                    "stars": repo["stargazers_count"],
                    "language": lang,
                    "description": repo["description"]
                })

        # Sort languages by count
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        top_langs = [l[0] for l in sorted_langs[:3]]

        return {
            "name": user_data.get("name") or username,
            "avatar_url": user_data.get("avatar_url"),
            "bio": user_data.get("bio"),
            "location": user_data.get("location"),
            "public_repos": user_data.get("public_repos"),
            "followers": user_data.get("followers"),
            "top_repos": top_repos,
            "top_languages": top_langs
        }

@mcp.tool()
async def analyze_profile(github_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze GitHub profile using Gemini 2.5 Flash."""
    client = get_gemini_client()
    
    prompt = f"""
    Analyze this GitHub profile data and return a JSON object with:
    - developer_vibe: A 1-sentence personality description.
    - top_skills: A list of 3 key skills/technologies inferred.
    - fun_fact: A clever observation based on their repos or bio.
    - card_theme: One of ["hacker", "builder", "researcher", "designer", "open-source-hero"].

    Profile Data:
    {json.dumps(github_data, indent=2)}

    Return ONLY raw JSON.
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash", # Using flash as requested
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    return json.loads(response.text)

@mcp.tool()
async def generate_card_html(username: str, github_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """Generate a self-contained HTML dev card."""
    theme = analysis.get("card_theme", "builder")
    
    themes = {
        "hacker": {"bg": "#0d1117", "text": "#58a6ff", "accent": "#238636", "border": "#30363d"},
        "builder": {"bg": "#f6f8fa", "text": "#24292f", "accent": "#0969da", "border": "#d0d7de"},
        "researcher": {"bg": "#ffffff", "text": "#1a1a1a", "accent": "#663399", "border": "#e1e4e8"},
        "designer": {"bg": "#fff5f5", "text": "#d73a49", "accent": "#ea4aaa", "border": "#ffdce0"},
        "open-source-hero": {"bg": "#f0fff4", "text": "#22863a", "accent": "#28a745", "border": "#dcffe4"}
    }
    
    colors = themes.get(theme, themes["builder"])
    
    repos_html = ""
    for repo in github_data.get("top_repos", [])[:3]:
        repos_html += f"""
        <div style="margin-top: 10px; padding: 8px; border: 1px solid {colors['border']}; border-radius: 6px;">
            <div style="font-weight: bold; color: {colors['accent']};">{repo['name']}</div>
            <div style="font-size: 0.8em; margin: 4px 0;">{repo.get('description') or 'No description'}</div>
            <div style="font-size: 0.75em; color: #666;">⭐ {repo['stars']} | {repo['language']}</div>
        </div>
        """

    skills_html = "".join([f'<span style="background: {colors["accent"]}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.7em; margin-right: 5px;">{s}</span>' for s in analysis.get("top_skills", [])])

    html = f"""
    <div style="width: 400px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background: {colors['bg']}; color: {colors['text']}; border: 1px solid {colors['border']}; border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <img src="{github_data['avatar_url']}" style="width: 60px; height: 60px; border-radius: 50%; border: 2px solid {colors['accent']}; margin-right: 15px;">
            <div>
                <div style="font-size: 1.2em; font-weight: bold;">{github_data['name']}</div>
                <div style="font-size: 0.8em; opacity: 0.8;">@{username}</div>
            </div>
        </div>
        <div style="font-size: 0.9em; font-style: italic; margin-bottom: 10px;">"{analysis['developer_vibe']}"</div>
        <div style="margin-bottom: 15px;">{skills_html}</div>
        <div style="display: flex; gap: 20px; font-size: 0.85em; margin-bottom: 15px; border-top: 1px solid {colors['border']}; border-bottom: 1px solid {colors['border']}; padding: 10px 0;">
            <div><strong>{github_data['public_repos']}</strong> Repos</div>
            <div><strong>{github_data['followers']}</strong> Followers</div>
            <div>Theme: <strong>{theme}</strong></div>
        </div>
        <div style="font-size: 0.9em; font-weight: bold; margin-bottom: 5px;">Top Repositories</div>
        {repos_html}
        <div style="margin-top: 15px; font-size: 0.75em; text-align: center; color: #888;">{analysis['fun_fact']}</div>
    </div>
    """
    return html

@mcp.tool()
async def save_card(username: str, html: str) -> str:
    """Save the HTML dev card to a file."""
    static_dir = Path("static/cards")
    static_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = static_dir / f"{username}.html"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return f"/static/cards/{username}.html"

if __name__ == "__main__":
    mcp.run()
