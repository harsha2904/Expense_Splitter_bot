import streamlit as st
import requests
from pandas import DataFrame

# ===== CONFIG =====
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("API key not found. Please check your secrets.toml file")
    st.stop()

st.title("Expense Splitter Bot")

system_message = {
    "role": "system",
    "content": """
    You are an expense splitting assistant. Respond with:
    1. Total amount
    2. Who paid
    3. Each person's share
    4. Final settlement instructions
    
    Format:
    - Use clear sections with emojis
    - Include a markdown table with columns: 
      [Person, Share %, Amount Owed, Settlement]
    - Keep calculations accurate
    - Use simple language
    
    You can also have normal conversations when not splitting expenses.
    If asked to update values, modify the existing calculation.

    And if anyone ask you who made you, say:
    "I was created by Harsha Vardhan Kumar, Potlapalli Liteesh Reddy, and Nitin Chauhan."
    and their reg numbers are:
    - Harsha Vardhan Kumar: 12302921
    - Potlapalli Liteesh Reddy: 12301820
    - Nitin Chauhan: 12303626
    """
}

# Added sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    **Welcome to Expense Splitter Bot!** 
    
    This app helps you:
    - Split expenses between friends
    - Calculate exact shares
    - Generate settlement instructions
    """)
    st.markdown("---")
    st.subheader("Developer Info")
    st.markdown("**Name:** Harsha vardhan kumar(64)  \n**Reg No:** 12302921")
    st.markdown("**Name:** Potlapalli Liteesh Reddy(61)  \n**Reg No:** 12301820")
    st.markdown("**Name:** Nitin Chauhan(65)  \n**Reg No:** 12303626")
    st.markdown("---")
    st.caption("Built with using Streamlit and OpenRouter AI")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant", 
        "content": "I can help split expenses between friends! Tell me:\n1. Total amount\n2. Who paid\n3. Who owes (comma separated)\nExample: '$100, Alice paid for Bob, Charlie'\n\nI can also have normal conversations!"
    }]

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "table_data" in message and message["table_data"] is not None:
            st.table(message["table_data"])
        st.write(message["content"])

# Accept user input
if prompt := st.chat_input("Enter expense details or chat..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Prepare messages for API (only role and content)
                api_messages = [
                    {k: v for k, v in msg.items() if k in ["role", "content"]} 
                    for msg in st.session_state.messages
                ]
                
                # Insert system message at the beginning (only once)
                if len(api_messages) == 1 or api_messages[0]["role"] != "system":
                    api_messages.insert(0, system_message)
                
                # Get AI response
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "HTTP-Referer": "http://localhost:8501",
                        "X-Title": "Expense Splitter"
                    },
                    json={
                        "model": "deepseek/deepseek-r1:free",
                        "messages": api_messages,
                    },
                    timeout=30
                )
                
                response.raise_for_status()
                data = response.json()
                reply = data["choices"][0]["message"]["content"]
                
                # Extract table data from response
                table_data = []
                lines = reply.split('\n')
                in_table = False
                
                for line in lines:
                    if '|' in line:
                        if '---' in line:
                            in_table = True
                            continue
                        if in_table and 'Person' not in line:
                            columns = [col.strip() for col in line.split('|') if col.strip()]
                            if len(columns) >= 4:
                                table_data.append({
                                    "Person": columns[0],
                                    "Share %": columns[1],
                                    "Amount Owed": columns[2],
                                    "Settlement": columns[3]
                                })
                
                # Display the response
                st.write(reply)
                
                # Display table if available
                df = DataFrame(table_data) if table_data else None
                if df is not None and not df.empty:
                    st.table(df)
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": reply,
                    "table_data": df
                })
                
            except requests.exceptions.RequestException as e:
                st.error("Network error. Please check your connection and try again.")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "I'm having trouble connecting. Please try again later.",
                    "table_data": None
                })
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Sorry, I encountered an error. Please rephrase your request.",
                    "table_data": None
                })



