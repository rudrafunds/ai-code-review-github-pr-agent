from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import os
from agent import run_pr_agent
from github import Github

app = FastAPI()

class WebhookPayload(BaseModel):
    action: str
    pull_request: dict
    repository: dict

@app.post("/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    
    # Support both webhook events and manual testing
    if "pull_request" not in payload:
        return {"error": "Not a PR event"}, 400
        
    if payload.get("action") not in ["opened", "synchronize", "reopened"]:
        return {"status": "ignored"}

    pr = payload["pull_request"]
    repo_name = payload["repository"]["full_name"]
    pr_number = pr["number"]
    installation_id = payload.get("installation", {}).get("id")

    print(f"Processing PR #{pr_number} in {repo_name} by {pr['user']['login']}")

    # Fire and forget
    asyncio.create_task(
        run_pr_agent(repo_name, pr_number, pr)
    )
    return {"status": "agent started", "repo": repo_name, "pr": pr_number}

@app.post("/analyze")
async def manual_analyze(repo: str, pr: int):
    """Call this from browser or curl to analyze any PR instantly"""
    print(f"Manual analysis: {repo} #{pr}")
    asyncio.create_task(run_pr_agent(repo, pr, None))
    return {"status": "started", "repo": repo, "pr": pr}

@app.get("/")
def home():
    return {"message": "PR-Agent Pro is alive! Ready for interview demo"}