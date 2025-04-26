import functools
import os

import streamlit as st
from dotenv import load_dotenv

from ask_your_neighbour.conversation_state import ConversationState
from ask_your_neighbour.gataway import user_query
from ask_your_neighbour.utils import LOGGER


# Load environment variables from .env file
@functools.lru_cache(maxsize=1)
def load_environment():
    # Try to load from .env file
    env_loaded = load_dotenv()

    if env_loaded:
        LOGGER.info("Environment variables loaded from .env file")
    else:
        LOGGER.warning("No .env file found or could not load environment variables")

    # Check if OPENAI_API_KEY is set
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OPENAI_API_KEY is not set. Please set it in your .env file or environment variables.")


def main():
    # Load environment variables
    load_environment()

    st.set_page_config(page_title="Ask your future neighbour", page_icon="💬", layout="centered")

    st.title("Ask Your Neighbour Chat")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_state" not in st.session_state:
        st.session_state.conversation_state = ConversationState()

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt_struct := st.chat_input("What would you like to ask?", accept_file=True):
        user_prompt = prompt_struct["text"]  # it should always be populated
        user_message = {"role": "user", "content": user_prompt}
        files = prompt_struct.get("files", [])
        LOGGER.info(f"User prompt: {user_prompt}, files: {files}.")

        # Add user message to chat history
        st.session_state.messages.append(user_message)
        st.session_state.conversation_state.all_messages.append(user_message)
        st.session_state.conversation_state.files.extend(files)

        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = user_query(st.session_state.conversation_state)
            LOGGER.info(f"Assistant response: {response}")
            st.markdown(response)

            if st.session_state.conversation_state.image is not None:
                st.image(st.session_state.conversation_state.image, use_container_width=True)
                st.session_state.conversation_state.image = None

        # Add assistant response to chat history
        assistant_message = {"role": "assistant", "content": response}
        st.session_state.messages.append(assistant_message)
        st.session_state.conversation_state.all_messages.append(assistant_message)


if __name__ == "__main__":
    main()
