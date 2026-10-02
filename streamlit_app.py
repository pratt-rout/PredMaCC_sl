import streamlit as st

st.set_page_config(page_title="PredMaCC", page_icon=":rocket:")


def health() -> dict:
    """Equivalent of GET /api/health"""
    return {"status": "ok"}


def hello() -> dict:
    """Equivalent of GET /api/hello"""
    return {"message": "Hello from FastAPI running on SPCS!"}


def echo(message: str) -> dict:
    """Equivalent of POST /api/echo"""
    return {"echo": message}


st.title("PredMaCC")

health_status = health()
st.caption(f"Backend status: {health_status['status']}")

hello_response = hello()
st.write(f"Backend says: {hello_response['message']}")

echo_input = st.text_input("Type a message", key="echo_input")
if st.button("Echo"):
    echo_response = echo(echo_input)
    st.write(f"Echo response: {echo_response['echo']}")
