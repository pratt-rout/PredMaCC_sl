import streamlit as st

from agents import AGENTS
from agents.auto_router import auto_router, auto_run

st.header("AI Assistant")

agent_name = st.sidebar.selectbox("Agent", list(AGENTS))
agent = AGENTS[agent_name]

history = st.session_state.setdefault(f"chat_{agent_name}", [])
if st.sidebar.button("Clear chat"):
    history.clear()

st.subheader(agent.name)
st.caption(agent.description)


def render(msg: dict) -> None:
    st.markdown(msg["content"])
    for spec in msg.get("charts", []):
        st.vega_lite_chart(spec, use_container_width=True)
    if msg.get("tools"):
        st.caption("Tools used: " + ", ".join(msg["tools"]))
    if msg.get("suggestions"):
        st.caption("You could also ask: " + " | ".join(msg["suggestions"]))


for msg in history:
    with st.chat_message(msg["role"]):
        render(msg)

if not history and agent.starter_questions:
    st.markdown("**Try asking:**")
    for i, q in enumerate(agent.starter_questions):
        if st.button(q, key=f"starter_{agent_name}_{i}"):
            st.session_state["_pending_question"] = q
            st.rerun()

pending = st.session_state.pop("_pending_question", None)
user_input = st.chat_input(f"Ask the {agent.name}...") or pending

if user_input:
    history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("The agent is working..."):
            reply = auto_run(history) if agent is auto_router else agent.run(history)
        message = {
            "role": "assistant",
            "content": reply.text,
            "charts": reply.charts,
            "tools": reply.tools,
            "suggestions": reply.suggestions,
        }
        render(message)
    history.append(message)
