import sys
from pathlib import Path

# Add project root to Python path
ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.agent import SupportAgent
from app.session import Session


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Aster & Row Support Agent",
    page_icon="🛍️",
    layout="centered",
)


# --------------------------------------------------
# Styling
# --------------------------------------------------

st.markdown(
    """
    <style>

    .main {
        max-width: 900px;
        margin: auto;
    }

    .title {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #666;
        font-size: 16px;
        margin-bottom: 25px;
    }

    .source-box {
        background-color: #f5f5f5;
        padding: 12px;
        border-radius: 8px;
        margin-top: 10px;
        font-size: 14px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Initialize agent/session
# --------------------------------------------------

if "agent" not in st.session_state:
    st.session_state.agent = SupportAgent()

if "session" not in st.session_state:
    st.session_state.session = Session(
        session_id="streamlit-user"
    )

if "messages" not in st.session_state:
    st.session_state.messages = []


agent = st.session_state.agent
session = st.session_state.session


# --------------------------------------------------
# Header
# --------------------------------------------------

st.markdown(
    '<div class="title">🛍️ Aster & Row Support Agent</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "AI-powered customer support for orders, returns, "
    "shipping, warranty and product questions."
    "</div>",
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:

    st.header("About")

    st.write(
        """
        This support agent uses:

        - 📚 Knowledge-base retrieval
        - 🤖 LLM reasoning
        - 📦 Order lookup tool
        - 🔒 Customer-data protection
        - 🛡️ Prompt-injection protection
        - 👨‍💼 Human handoff for exceptions
        """
    )

    st.divider()

    st.subheader("Example questions")

    examples = [
        "How long do I have to return an unused backpack?",
        "What is the return window for TrailPlus members?",
        "Where is ORD-1007?",
        "When should ORD-1007 arrive?",
        "What happens if my item is damaged?",
        "Do you ship to Canada?",
    ]

    for example in examples:
        st.write(f"• {example}")

    st.divider()

    if st.button("Clear conversation"):
        st.session_state.messages = []

        st.session_state.session = Session(
            session_id="streamlit-user"
        )

        st.rerun()


# --------------------------------------------------
# Display previous messages
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --------------------------------------------------
# Chat input
# --------------------------------------------------

user_message = st.chat_input(
    "Ask about an order, return, shipping, warranty..."
)


if user_message:

    # Display user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_message)

    # Get agent response
    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                response = agent.handle(
                    session,
                    user_message,
                )

                answer = response.answer

            except Exception as error:

                answer = (
                    "Sorry, I encountered an error while "
                    "processing your request."
                )

                st.error(str(error))

        st.markdown(answer)

        # Show sources if available
        if getattr(response, "sources", None):

            with st.expander("View sources"):

                for source in response.sources:
                    st.write(f"📄 {source}")

        # Show handoff information
        if getattr(response, "handoff", False):

            st.warning(
                "This request requires human support review."
            )

    # Save assistant response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )