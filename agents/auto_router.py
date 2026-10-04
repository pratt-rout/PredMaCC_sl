"""Auto-router: uses Cortex COMPLETE to pick the best agent for a query."""

from agents.base import Agent, Reply, get_session
from agents.health_analyst import health_analyst
from agents.knowledge import maintenance_knowledge
from agents.root_cause import root_cause_investigator

_AGENTS_BY_KEY = {
    "health": health_analyst,
    "root_cause": root_cause_investigator,
    "knowledge": maintenance_knowledge,
}

_CLASSIFY_PROMPT = f"""You are a router. Given a user question, reply with ONLY one of these keys:
- health — {health_analyst.description}
- root_cause — {root_cause_investigator.description}
- knowledge — {maintenance_knowledge.description}

Reply with the single key word, nothing else."""


def _pick_agent(query: str) -> Agent:
    session = get_session()
    prompt = f"{_CLASSIFY_PROMPT}\n\nUser question: {query}"
    raw = session.sql(
        "SELECT SNOWFLAKE.CORTEX.COMPLETE('openai-gpt-5-mini', ?) AS R",
        params=[prompt],
    ).collect()[0]["R"]
    key = raw.strip().strip('"').strip().lower()
    return _AGENTS_BY_KEY.get(key, health_analyst)


auto_router = Agent(
    name="Auto (Smart Router)",
    description="Automatically picks the best agent for your question.",
    agent_fqn="",
    starter_questions=[
        "Why did DIE-003 fail on 2024-01-10?",
        "Which die has the most downtime?",
        "What is the procedure for guide pin realignment?",
    ],
)


def auto_run(history: list, scope: str = "") -> Reply:
    """Route to one agent and run it. Never raises — mirrors Agent.run's contract."""
    query = history[-1]["content"]
    note = ""
    try:
        chosen = _pick_agent(query)
    except Exception as e:
        chosen = health_analyst
        note = f"Router unavailable ({e}) — fell back to {chosen.name}."

    reply = chosen.run(history, scope)
    reply.routed_to = note or f"Routed to {chosen.name}"
    return reply
