from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os
from pathlib import Path

from agent import run_agent_workflow

app = FastAPI(title="GitHub Dev Card Generator API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists
static_path = Path("static/cards")
static_path.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class CardRequest(BaseModel):
    username: str

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/generate")
async def generate_card(request: CardRequest):
    try:
        # Run the agent workflow
        result_message = await run_agent_workflow(request.username)
        
        if result_message.startswith("Error:"):
            raise HTTPException(status_code=404, detail=result_message)

        card_url = f"/static/cards/{request.username}.html"
        
        return {
            "status": "success",
            "username": request.username,
            "card_url": card_url,
            "message": result_message
        }
    except Exception as e:
        print(f"Error generating card: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/card/{username}")
async def get_card(username: str):
    file_path = static_path / f"{username}.html"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Card not found")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return {"html": f.read()}

if __name__ == "__main__":
    # Cloud Run provides the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
