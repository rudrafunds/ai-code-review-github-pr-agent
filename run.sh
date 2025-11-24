# 1. Start server
uvicorn main:app --reload

# 2. In another terminal, expose (optional, only if using real webhook)
ngrok http 8000

# 3. Trigger analysis on any PR instantly
curl -X POST "http://localhost:8000/analyze?repo=rudrafunds/ai-code-review-github-pr-agent&pr=1"
# or open in browser: http://localhost:8000/analyze?repo=YOURUSER/YOURREPO&pr=1