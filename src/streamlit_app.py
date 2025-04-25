import streamlit as st
from ask_your_neighbour.utils import LOGGER

def main():
    st.set_page_config(
        page_title="Ask Your Neighbour Chat",
        page_icon="💬",
        layout="centered"
    )
    
    st.title("Ask Your Neighbour Chat")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Accept user input
    if prompt := st.chat_input("What would you like to ask?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response = f"Hello! You asked: {prompt}"
            st.markdown(response)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        LOGGER.info(f"User prompt: {prompt}")
        LOGGER.info(f"Assistant response: {response}")

if __name__ == "__main__":
    main() 