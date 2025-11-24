async def get_pr_diff(repo_name, pr_number):
    return "Sample diff..."  # In real use GitHub API

async def is_first_time_contributor(repo_name, username):
    # Simple heuristic for demo
    return username in ["new-contributor-demo", "john-doe", "jane-doe"]

async def get_onboarding_context(repo_name):
    return """
# Project Overview
Fast-moving Python backend. Uses FastAPI + SQLAlchemy.
Key files: app/main.py, app/models.py
Ask in #backend-help channel.
Code style: Black + Ruff
"""