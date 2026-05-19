import asyncio
import os
import json
from dotenv import load_dotenv
from mcp_server import scrape_github, analyze_profile, generate_card_html, save_card

# Load environment variables
load_dotenv()

async def test_end_to_end():
    username = "torvalds"
    print(f"--- Step 1: Scraping GitHub for {username} ---")
    try:
        github_data = await scrape_github(username)
        if "error" in github_data:
            print(f"Error in scrape_github: {github_data['error']}")
            return
        print("Success: GitHub data retrieved.")
    except Exception as e:
        print(f"Failed to scrape GitHub: {str(e)}")
        return

    print("\n--- Step 2: Analyzing Profile with Gemini ---")
    try:
        analysis = await analyze_profile(github_data)
        print("Success: Analysis complete.")
    except Exception as e:
        print(f"Failed to analyze profile: {str(e)}")
        return

    print("\n--- Step 3: Generating HTML Card ---")
    try:
        card_html = await generate_card_html(username, github_data, analysis)
        print("Success: HTML generated.")
    except Exception as e:
        print(f"Failed to generate card HTML: {str(e)}")
        return

    print("\n--- Step 4: Final Results ---")
    print(f"Card Theme: {analysis.get('card_theme')}")
    print(f"Developer Vibe: {analysis.get('developer_vibe')}")

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
