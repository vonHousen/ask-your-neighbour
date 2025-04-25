import functools
import streamlit as st
import os
from dotenv import load_dotenv

from ask_your_neighbour.utils import LOGGER
from ask_your_neighbour.gataway import user_query


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
    
    st.set_page_config(
        page_title="Ask Your Neighbour Chat",
        page_icon="💬",
        layout="centered"
    )
    
    st.title("Ask Your Neighbour Chat")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "files" not in st.session_state:
        st.session_state.files = []
    
    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Accept user input
    if prompt_struct := st.chat_input("What would you like to ask?", accept_file=True):
        prompt = prompt_struct.get("text", "")
        files = prompt_struct.get("files", [])
        
        LOGGER.info(f"User prompt: {prompt}, files: {files}.")

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.files.extend(files)

        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = user_query(prompt, st.session_state.files)
            LOGGER.info(f"Assistant response: {response}")
            st.markdown(response)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 