# PR-Agent Pro – Smart Code Review & Onboarding Agent

**User Problem**  
Engineers waste 5–15 hours/week writing repetitive code reviews and onboarding new contributors. Tribal knowledge is trapped in seniors’ heads.

**Solution**  
A GitHub App that instantly:
• Analyzes any PR with full repo context
• Posts high-quality, line-specific review comments
• Detects first-time contributors and auto-generates personalized onboarding guides

**Success Metrics (Demo will prove)**
- <20 second end-to-end review
- ≥85% of comments rated “useful” or better by senior engineers
- Onboarding summary contains zero hallucinations (verified live)

**Constraints**
- Runs on laptop or $5/month cloud
- Uses only public APIs + Anthropic/OpenAI
- Read-only by default, human approval before posting
- Fully open-source, no enterprise lock-in

**Impact**  
Turns a 2-hour manual review → 18 seconds of AI + 5 minutes human approval.

## Design
**Agentic Workflow & MCP (Multi-step Chain-of-Thought with Planning & Reflection)**  
Built with **LangGraph** → true stateful agent (not simple chain):
- ReAct-style loop with explicit planning step  
- Self-critique prompt forces the model to verify line numbers and file existence  
- Conditional branching (onboarding only for first-time contributors)  
- All tool calls are real Python functions (no fake stubs in final version)

**Model Choice**  
Claude 3.5 Sonnet (2024-10-22) – 200k context, best-in-class code reasoning, lowest cost/quality ratio.

**Tooling Stack** (all free or pay-as-you-go)
- FastAPI + Uvicorn (local)  
- LangGraph + LangChain community  
- PyGithub for real GitHub interaction  
- Claude via Anthropic API (~$0.04 per full review)  
- Optional: OpenAI GPT-4o or Groq Llama3 as drop-in replacement

**Risk Controls & Safety**
- Human-in-the-loop ready (can switch to draft reviews)  
- Hallucination guard: model must quote exact line numbers  
- Cost caps via environment variables  
- Secrets in `.env`
  
**Monitoring**  
- Console logs + optional LangSmith tracing
- Token usage printed per run

**Deployment Plan**
```bash
uvicorn main:app --reload
# Then trigger any PR instantly:

curl "http://localhost:8000/analyze?repo=owner/repo&pr=123"

