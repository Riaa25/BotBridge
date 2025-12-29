import streamlit as st
import os
import time
from openai import OpenAI
from agents import PersonalAgent

# --- 1. SETUP ---
st.set_page_config(page_title="BotBridge", page_icon="🤝", layout="wide")

@st.cache_resource
def get_global_db():
    # 'rooms' stores user notes, 'config' stores passwords/API keys
    return {"rooms": {}, "config": {}}

data = get_global_db()

# --- 2. ROOM & URL LOGIC ---
room_id = st.query_params.get("room", "Hackathon_Room")

if room_id not in data["rooms"]:
    data["rooms"][room_id] = {}

# --- 3. SIDEBAR (The Lockbox) ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    
    st.title("🛡️ Room Control")
    
    # Check if room is already set up by a host
    is_setup = room_id in data["config"]
    
    if not is_setup:
        st.subheader("🆕 Host Setup")
        host_pass = st.text_input("Create Room Password", type="password")
        gsk_key = st.text_input("Enter Groq API Key", type="password")
        
        if st.button("🚀 Initialize Room"):
            if host_pass and gsk_key:
                data["config"][room_id] = {"pass": host_pass, "key": gsk_key}
                st.success("Room is now LIVE!")
                st.rerun()
            else:
                st.error("Please provide both a password and API key.")
    else:
        st.success("✅ Room is Secure & Active")
        # Hidden Admin Section
        with st.expander("🔑 Host Login"):
            check_pass = st.text_input("Verify Password", type="password")
            if check_pass == data["config"][room_id]["pass"]:
                st.info("Host Mode Active")
                if st.button("Reset Room (Clear Data)"):
                    data["rooms"][room_id] = {}
                    st.rerun()
            elif check_pass:
                st.error("Wrong Password")

    st.divider()
    st.write("🔗 **Share Link:**")
    # Replace with your actual deployed URL
    base_url = "https://botbridge-8xrpg3dwkymoexafjmvfgz.streamlit.app"
    st.code(f"{base_url}/?room={room_id}")

# --- 4. MAIN INTERFACE (For Everyone) ---
st.title(f"📱 Room: {room_id}")

if not is_setup:
    st.warning("Waiting for the Host to initialize the room...")
    st.stop() # Stops the rest of the page from loading for guests

# Guest/User Flow
user_name = st.text_input("1. Your Name:", placeholder="e.g., Alice")

if user_name:
    st.subheader(f"Welcome, {user_name}")
    user_notes = st.text_area("2. Your Private Preferences:", 
                              value=data["rooms"][room_id].get(user_name, ""),
                              placeholder="e.g., I'm allergic to peanuts and free at 8pm.")
    
    if st.button("💾 Submit to Group"):
        data["rooms"][room_id][user_name] = user_notes
        st.success("Saved! Waiting for the group to be ready...")

# --- 5. THE AI NEGOTIATOR ---
st.divider()
participants = list(data["rooms"][room_id].keys())
st.write(f"👥 **Joined:** {', '.join(participants) if participants else 'Waiting for people...'}")

if len(participants) >= 2:
    if st.button("🤖 Start AI Negotiation", type="primary"):
        # Uses the host's key stored in the global config
        api_key = data["config"][room_id]["key"]
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
        
        agents = [PersonalAgent(name, notes, client) for name, notes in data["rooms"][room_id].items()]
        
        chat_log = "Discussion started."
        with st.status("Agents are debating..."):
            for i in range(2): # 2 rounds
                for agent in agents:
                    res = agent.negotiate(chat_log)
                    st.chat_message("user", avatar="🤖").write(f"**{agent.name}:** {res['message']}")
                    chat_log += f"\n{agent.name}: {res['message']}"
                    if res['status'] == "ACCEPT":
                        st.balloons()
                        st.success(f"Agreement Reached: {res['proposal']}")
                        st.stop()
