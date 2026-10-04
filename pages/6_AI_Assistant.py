import streamlit as st

from agents import AGENTS
from agents.auto_router import auto_router, auto_run
from utils.ui import tall_sidebar_nav

tall_sidebar_nav()

st.header("AI Assistant")

agent_name = st.sidebar.selectbox("Agent", list(AGENTS))
agent = AGENTS[agent_name]

history = st.session_state.setdefault(f"chat_{agent_name}", [])
if st.sidebar.button("Clear chat"):
    history.clear()
    st.experimental_rerun()

st.subheader(agent.name)
st.caption(agent.description)


def render(msg: dict) -> None:
    role = msg["role"]
    prefix = "**You:**" if role == "user" else "**Assistant:**"
    st.markdown(f"{prefix} {msg['content']}")
    for spec in msg.get("charts", []):
        st.vega_lite_chart(spec, use_container_width=True)
    if msg.get("tools"):
        st.caption("Tools used: " + ", ".join(msg["tools"]))
    if msg.get("suggestions"):
        st.caption("You could also ask: " + " | ".join(msg["suggestions"]))
    st.markdown("---")


for msg in history:
    render(msg)

# Starter questions (only when chat is empty)
if not history and agent.starter_questions:
    st.markdown("**Try asking:**")
    for i, q in enumerate(agent.starter_questions):
        if st.button(q, key=f"starter_{agent_name}_{i}"):
            st.session_state["_pending_question"] = q
            st.experimental_rerun()

# Input area
pending = st.session_state.pop("_pending_question", None)
if pending:
    user_input = pending
    send = True
else:
    user_input = st.text_input(f"Ask the {agent.name}...", key=f"input_{agent_name}")
    send = st.button("Send")

if send and user_input:
    history.append({"role": "user", "content": user_input})
    with st.spinner("The agent is working..."):
        reply = auto_run(history) if agent is auto_router else agent.run(history)
    history.append(
        {
            "role": "assistant",
            "content": reply.text,
            "charts": reply.charts,
            "tools": reply.tools,
            "suggestions": reply.suggestions,
        }
    )
    st.experimental_rerun()
