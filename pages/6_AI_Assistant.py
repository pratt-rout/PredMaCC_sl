import streamlit as st

from agents import AGENTS
from agents.auto_router import auto_router, auto_run
from agents.base import clear_threads
from utils.ui import tall_sidebar_nav

tall_sidebar_nav()

st.header("AI Assistant")

agent_name = st.sidebar.selectbox("Agent", list(AGENTS))
agent = AGENTS[agent_name]

HISTORY_KEY = f"chat_{agent_name}"
INPUT_KEY = f"input_{agent_name}"
SUBMIT_KEY = f"_submit_{agent_name}"
CLEAR_KEY = f"_clear_{agent_name}"

# Reset the box before the widget exists — session_state for a widget key
# cannot be changed once that widget has been created in this run.
if st.session_state.pop(CLEAR_KEY, False):
    st.session_state[INPUT_KEY] = ""

history = st.session_state.setdefault(HISTORY_KEY, [])

if st.sidebar.button("Clear chat"):
    history.clear()
    st.session_state[INPUT_KEY] = ""
    st.session_state.pop(SUBMIT_KEY, None)
    clear_threads(agent_name)
    st.experimental_rerun()

st.subheader(agent.name)
st.caption(agent.description)


def prefill(question: str) -> None:
    """Put a question in the input box and let the user send it."""
    st.session_state[INPUT_KEY] = question
    st.experimental_rerun()


def render(msg: dict, idx: int, is_last: bool) -> None:
    prefix = "**You:**" if msg["role"] == "user" else "**Assistant:**"
    st.markdown(f"{prefix} {msg['content']}")
    if msg.get("routed_to"):
        st.caption(msg["routed_to"])
    for spec in msg.get("charts", []):
        st.vega_lite_chart(spec, use_container_width=True)
    if msg.get("tools"):
        st.caption("Tools used: " + ", ".join(msg["tools"]))
    if msg.get("suggestions"):
        st.markdown("**You could also ask:**")
        for j, suggestion in enumerate(msg["suggestions"]):
            if is_last:
                if st.button(suggestion, key=f"sugg_{agent_name}_{idx}_{j}"):
                    prefill(suggestion)
            else:
                st.markdown(f"- {suggestion}")
    st.markdown("---")


for i, msg in enumerate(history):
    render(msg, i, is_last=(i == len(history) - 1))

# Starter questions, shown only while the chat is empty.
if not history and agent.starter_questions:
    st.markdown("**Try asking:**")
    for i, question in enumerate(agent.starter_questions):
        if st.button(question, key=f"starter_{agent_name}_{i}"):
            prefill(question)


def _on_enter() -> None:
    st.session_state[SUBMIT_KEY] = True


user_input = st.text_input(f"Ask the {agent.name}...", key=INPUT_KEY, on_change=_on_enter)
send = st.button("Send") or st.session_state.pop(SUBMIT_KEY, False)

if send and user_input.strip():
    history.append({"role": "user", "content": user_input.strip()})
    with st.spinner("The agent is working..."):
        if agent is auto_router:
            reply = auto_run(history, agent_name)
        else:
            reply = agent.run(history, agent_name)
    history.append(
        {
            "role": "assistant",
            "content": reply.text,
            "charts": reply.charts,
            "tools": reply.tools,
            "suggestions": reply.suggestions,
            "routed_to": reply.routed_to,
        }
    )
    st.session_state[CLEAR_KEY] = True
    st.experimental_rerun()
