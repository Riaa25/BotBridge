import streamlit as st
from openai import OpenAI
from agents import PersonalAgent
import time

st.set_page_config(page_title="BotBridge Group", layout="wide")

# --- GLOBAL DATABASE SIMULATION ---
# This allows data to persist across different users/tabs in the same session
if "db" not in st.session_state:
    st.session_state.db = {} # Format: {room_id: {user_name: notes}}

# --- URL / ROOM LOGIC ---
query_params = st.query_params
room_id = query_params.get("room", "General_Room")

if room_id not in st.session_state.db:
    st.session_state.db[room_id] = {}

# --- SIDEBAR ---
with st.sidebar:
    st.title("🤝 BotBridge")
    st.write(f"📍 **Room ID:** `{room_id}`")
    
    # ONLY THE HOST NEEDS TO ENTER THIS
    gsk_key = st.text_input("Host API Key (Groq)", type="password", help="Only needed to start negotiation")
    
st.divider()
    # --- DYNAMIC INVITE LINK GENERATOR ---
    # This automatically detects if you are on localhost or Streamlit Cloud
    try:
        # Get the actual URL from the browser (works on deployed apps)
        from streamlit.components.v1 import html
        
        # We can use a simpler trick for Hackathons:
        # If the URL is localhost, use that; otherwise, default to your public domain
        current_url = "https://botbridge.streamlit.app" # <--- REPLACE WITH YOUR DEPLOYED URL
        
        st.write("🔗 **Invite Friends:**")
        invite_link = f"{current_url}/?room={room_id}"
        st.code(invite_link)
        st.caption("Share this link with your friends!")
    except:
        st.write("🔗 **Invite Link (Local):**")
        st.code(f"http://localhost:8501/?room={room_id}")

# --- MAIN INTERFACE ---
st.title(f"📱 Group Room: {room_id}")

# 1. User Joins
user_name = st.text_input("Enter Your Name to Join:", placeholder="e.g. Alice")

if user_name:
    # 2. User Writes Private Notes
    # We load existing notes if they already saved some
    existing_notes = st.session_state.db[room_id].get(user_name, "")
    user_notes = st.text_area(f"Hello {user_name}, write your private constraints here:", 
                              value=existing_notes,
                              height=150)
    
    if st.button("✅ Save My Notes to Group"):
        st.session_state.db[room_id][user_name] = user_notes
        st.success(f"Notes for {user_name} are secured in the cloud!")

st.divider()

# 3. View Participants
participants = list(st.session_state.db[room_id].keys())
st.write(f"👥 **Ready to Negotiate:** {', '.join(participants) if participants else 'Waiting for people...'}")

# 4. The Negotiation (Run by Host)
if st.button("🚀 Start Group Negotiation"):
    if not gsk_key:
        st.error("The Host must provide a Groq API Key to run the AI agents.")
    elif len(participants) < 2:
        st.error("At least 2 people must save notes before starting.")
    else:
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=gsk_key)
        agents = [PersonalAgent(name, notes, client) for name, notes in st.session_state.db[room_id].items()]
        
        chat_log = "Initial: Group wants to find a common plan."
        
        # UI for the Chat
        with st.container():
            st.subheader("💬 Live Discussion")
            for round_idx in range(2):
                for agent in agents:
                    with st.chat_message("user", avatar="🤖"):
                        res = agent.negotiate(chat_log)
                        st.write(f"**{agent.name}'s Assistant:** {res['message']}")
                        chat_log += f"\n{agent.name}: {res['message']} (Proposal: {res['proposal']})"
                        
                        if res['status'] == "ACCEPT":
                            st.success(f"🏆 FINAL AGREEMENT: {res['proposal']}")
                            st.balloons()
                            st.stop()

                    time.sleep(0.5)
