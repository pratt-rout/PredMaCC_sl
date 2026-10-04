"""Shared agent interface: calls deployed Cortex Agent objects via SNOWFLAKE.CORTEX.DATA_AGENT_RUN."""

import json
from dataclasses import dataclass, field

import streamlit as st

HIDDEN_TOOL_PREFIXES = ("system_", "server_skill")


class AgentError(Exception):
    pass


@dataclass
class Reply:
    text: str
    charts: list = field(default_factory=list)
    tools: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)


def get_session():
    """Snowpark session: active session on Snowflake, or an st.connection('snowflake') locally."""
    errors = []
    try:
        from snowflake.snowpark.context import get_active_session

        return get_active_session()
    except Exception as e:
        errors.append(f"get_active_session: {e}")
    try:
        return st.connection("snowflake").session()
    except Exception as e:
        errors.append(f"st.connection('snowflake'): {e}")
    raise AgentError(
        "No Snowflake session available. On Streamlit in Snowflake this is automatic. "
        "Locally, configure a connection for st.connection('snowflake') "
        "(see .streamlit/secrets.toml or SNOWFLAKE_DEFAULT_CONNECTION_NAME). Details: " + " | ".join(errors)
    )


def parse_response(raw: str) -> tuple:
    """Return (Reply, metadata) from a DATA_AGENT_RUN JSON string."""
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        raise AgentError(f"Unexpected response: {str(raw)[:300]}")
    if "content" not in data:
        raise AgentError(f"Agent returned no content: {str(raw)[:500]}")

    texts, charts, tools, suggestions = [], [], [], []
    for block in data["content"]:
        kind = block.get("type")
        if kind == "text":
            texts.append(block.get("text", ""))
        elif kind == "chart":
            try:
                charts.append(json.loads(block["chart"]["chart_spec"]))
            except (KeyError, ValueError):
                pass
        elif kind == "tool_use":
            name = block.get("tool_use", {}).get("name", "")
            if name and not name.startswith(HIDDEN_TOOL_PREFIXES) and name not in tools:
                tools.append(name)
        elif kind == "suggested_queries":
            suggestions = [q["query"] for q in block.get("suggested_queries", []) if q.get("query")]

    text = "\n\n".join(t.strip() for t in texts if t.strip())
    for w in data.get("warnings", []):
        text += f"\n\n*Warning: {w.get('message', w)}*"
    if not text:
        text = "The agent did not return a text answer."
    return Reply(text=text, charts=charts, tools=tools, suggestions=suggestions), data.get("metadata", {})


@dataclass
class Agent:
    name: str
    description: str
    agent_fqn: str
    starter_questions: list = field(default_factory=list)

    @property
    def _thread_key(self) -> str:
        return f"_thread_{self.agent_fqn}"

    def run(self, history: list) -> Reply:
        """Send the latest user message to the agent. Multi-turn context is kept in a Cortex thread."""
        if len(history) <= 1:
            st.session_state.pop(self._thread_key, None)  # new conversation
        thread = st.session_state.get(self._thread_key)

        body = {
            "messages": [{"role": "user", "content": [{"type": "text", "text": history[-1]["content"]}]}]
        }
        if thread:
            body.update(thread)

        try:
            session = get_session()
            raw = session.sql(
                "SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(?, ?, ?) AS R",
                params=[self.agent_fqn, json.dumps(body), thread is None],
            ).collect()[0]["R"]
            reply, meta = parse_response(raw)
        except AgentError as e:
            return Reply(text=f"**{self.name} is unavailable.** {e}")
        except Exception as e:
            return Reply(
                text=(
                    f"**{self.name} call failed.** {e}\n\n"
                    "Check that the app's role has USAGE on the agent and its tools "
                    f"(`{self.agent_fqn}`) and the SNOWFLAKE.CORTEX_AGENT_USER database role."
                )
            )

        if meta.get("thread_id") and meta.get("assistant_message_id"):
            st.session_state[self._thread_key] = {
                "thread_id": meta["thread_id"],
                "parent_message_id": meta["assistant_message_id"],
            }
        return reply
