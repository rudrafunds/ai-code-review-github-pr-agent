from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from tools import get_pr_diff, get_file_content, search_codebase, is_first_time_contributor, get_onboarding_context
from github import Github
import os

# Choose model (Claude is best for code)
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.2)
# llm = ChatOpenAI(model="gpt-4o", temperature=0)

class AgentState(dict):
    pr_diff: str
    review_comments: str = ""
    onboarding_guide: str = ""
    repo_name: str
    pr_number: int
    author: str
    files_changed: list

async def plan_step(state: AgentState):
    prompt = f"""
You are an expert senior engineer reviewing PR #{state['pr_number']} in {state['repo_name']} by @{state['author']}.

PR Diff:
{state['pr_diff'][:100000]}  # Safe truncate

First, list the files that need deep review.
Then decide: is this user's first contribution? (you will get this info soon)
Finally, plan 2 parallel tasks: code review + onboarding if needed.
"""
    response = await llm.ainvoke([SystemMessage(content="You are a world-class code reviewer."), 
                                 HumanMessage(content=prompt)])
    print("Plan:", response.content)
    return {"plan": response.content}

async def review_step(state: AgentState):
    comments = []
    diff = state['pr_diff']
    
    # Self-critique + tool-use loop (MCP style)
    review_prompt = f"""
You are reviewing this diff. Be extremely precise. Quote exact line numbers.
Focus on: correctness, testing, security, naming, project conventions.

Diff:
{diff}

Rules:
- Never hallucinate file paths
- If unsure, say "I need to check file X" and use tools
- End with final review comment block
"""
    result = await llm.ainvoke([HumanMessage(content=review_prompt)])
    comments.append(result.content)
    
    return {"review_comments": "\n\n".join(comments)}

async def onboarding_step(state: AgentState):
    if not state.get("is_first_time"):
        return {"onboarding_guide": "Not first time contributor"}
    
    context = await get_onboarding_context(state['repo_name'])
    prompt = f"""
Generate a warm, personalized onboarding guide for @{state['author']} who just opened their first PR.

Include:
- Welcome message
- Link to README / CONTRIBUTING.md
- Key architecture points
- Common gotchas from this codebase
- Who to ping for help

Context from repo:
{context[:50000]}
"""
    result = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"onboarding_guide": result.content}

async def post_to_github(state: AgentState):
    token = os.getenv("GITHUB_TOKEN")
    g = Github(token)
    repo = g.get_repo(state['repo_name'])
    pr = repo.get_pull(state['pr_number'])
    
    comment_body = f"""
## PR-Agent Pro Review (PoC)

### Code Review
{state['review_comments']}

### Onboarding Guide (First-Time Contributor!)
{state['onboarding_guide']}
---
*This is an AI-generated review • Built for Technical Manager interview • Nov 2025*
"""
    pr.create_issue_comment(comment_body)
    print("Posted comment to GitHub!")
    return state

# Build the graph
workflow = StateGraph(AgentState)
workflow.add_node("plan", plan_step)
workflow.add_node("review", review_step)
workflow.add_node("onboarding", onboarding_step)
workflow.add_node("post", post_to_github)

workflow.set_entry_point("plan")
workflow.add_edge("plan", "review")
workflow.add_conditional_edges("review", lambda x: "onboarding" if x.get("is_first_time") else "post")
workflow.add_edge("onboarding", "post")
workflow.add_edge("post", END)

app = workflow.compile()

async def run_pr_agent(repo_name: str, pr_number: int, pr_data: dict = None):
    try:
        g = Github(os.getenv("GITHUB_TOKEN"))
        repo = g.get_repo(repo_name)
        pull = repo.get_pull(pr_number)
        
        # Get real diff
        files = pull.get_files()
        diff_lines = []
        for f in files:
            if f.patch:
                diff_lines.append(f"diff --git a/{f.filename} b/{f.filename}")
                diff_lines.append(f.patch)
        
        full_diff = "\n".join(diff_lines)[:120000]  # Stay under context limit
        
        # Detect first-time contributor
        author = pull.user.login
        past_prs = repo.get_pulls(state='all', head=f"{author}:")
        is_first_time = sum(1 for _ in past_prs) <= 1
        
        state = AgentState(
            pr_diff=full_diff or "No diff available",
            repo_name=repo_name,
            pr_number=pr_number,
            author=author,
            is_first_time=is_first_time,
            files_changed=[f.filename for f in files]
        )
        
        result = await app.ainvoke(state)
        print("Agent finished successfully!")
        
    except Exception as e:
        print("Agent error:", str(e))
        # Still post error comment (optional)
        if 'pull' in locals():
            pull.create_issue_comment(f"PR-Agent Pro Error: {str(e)}")