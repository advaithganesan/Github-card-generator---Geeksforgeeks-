import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Initialize the Gemini Client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

SYSTEM_INSTRUCTION = """
You are a GitHub profile analyst and dev card generator. 
When a user gives you a GitHub username, you ALWAYS follow this exact sequence: 
1. Call scrape_github(username)
2. Call analyze_profile(github_data) with the result from step 1
3. Call generate_card_html(username, github_data, analysis) with the results from 1 and 2
4. Call save_card(username, html) with the result from step 3

Never skip steps. Be enthusiastic about developers' work. 
If the profile is private or doesn't exist, say so clearly.
"""

# Manual tool definitions for the client since McpToolset is not available in all versions
# and to ensure stability across deployments.

async def run_agent_workflow(username: str):
    """
    Manually orchestrate the agent workflow since the ADK Runner is not available.
    """
    # Import tools here to avoid circular imports
    from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card

    # Step 1: Scrape
    print(f"Scraping {username}...")
    github_data = await scrape_github(username)
    if "error" in github_data:
        return f"Error: {github_data['error']}"

    # Step 2: Analyze
    print(f"Analyzing {username}...")
    analysis = await analyze_profile(github_data)

    # Step 3: Generate HTML
    print(f"Generating HTML for {username}...")
    html = await generate_card_html(username, github_data, analysis)

    # Step 4: Save
    print(f"Saving card for {username}...")
    url = await save_card(username, html)

    return f"Successfully generated card for {username}. View it at {url}"
