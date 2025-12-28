import streamlit as st
from openai import OpenAI
from agents import PersonalAgent
import time

# --- 1. SETUP & PAGE CONFIG ---
st.set_page_config(page_title="BotBridge", page_icon="🤝", layout="wide")
if os.path.exists("logo.png"):
    st.image("logo.png", width=200)
else:
    st.title("🤝 BotBridge") # Fallback title if image is missing
# --- 2. GLOBAL STORAGE (The "Cloud" Database) ---
# This dictionary is shared across ALL users and ALL tabs.
@st.cache_resource
def get_global_db():
    return {} # Format: {room_id: {user_name: private_notes}}

db = get_global_db()

# --- 3. URL & ROOM LOGIC ---
# Automatically detects if a user clicked a link with ?room=XYZ
room_id = st.query_params.get("room", "Default_Room")
if room_id not in db:
    db[room_id] = {}

# --- 4. SIDEBAR (The Control Center) ---
with st.sidebar:
    st.title("🤝 BotBridge Settings")
    st.info(f"📍 Current Room: **{room_id}**")
    
    # Only the host needs to provide the API key
    gsk_key = st.text_input("Host API Key (Groq)", type="password", help="Starts with gsk_")
    
    st.divider()
    
    # Dynamic Link Generator
    st.write("🔗 **Invite Participants:**")
    # This detects your public app URL automatically once deployed
    base_url = "https://botbridge.streamlit.app" 
    invite_link = f"{base_url}/?room={room_id}"
    st.code(invite_link)
    st.caption("Copy and send this link to your group!")

# --- 5. MAIN INTERFACE ---
st.title(f"📱 Group Planning: {room_id}")

# Step 1: Join the Group
user_name = st.text_input("1. Your Name", placeholder="e.g. Alice")

if user_name:
    # Step 2: Private Notes
    st.subheader(f"Welcome {user_name}!")
    # Load existing notes from the global database if they exist
    existing_notes = db[room_id].get(user_name, "")
    
    user_notes = st.text_area(
        "2. Your Private Constraints (What you want, what you hate):", 
        value=existing_notes,
        placeholder="e.g. I only eat Italian food. I'm free after 7pm."
    )
    
    if st.button("💾 Save My Notes"):
        db[room_id][user_name] = user_notes
        st.success("Your notes are saved in the room! Waiting for others...")

st.divider()

# Step 3: View the Group & Negotiate
participants = list(db[room_id].keys())

if len(participants) > 0:
    st.write(f"👥 **People in Room:** {', '.join(participants)}")
    
    if st.button("🚀 Start Group Negotiation", use_container_width=True):
        if not gsk_key:
            st.error("Please provide the Groq API Key in the sidebar.")
        elif len(participants) < 2:
            st.warning("Wait for at least one more person to join the room!")
        else:
            client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=gsk_key)
            agents = [PersonalAgent(name, notes, client) for name, notes in db[room_id].items()]
            
            chat_log = "Discussion started to find a group agreement."
            
            st.subheader("💬 Live Discussion")
            # The AI Loop
            for round_idx in range(2):
                for agent in agents:
                    with st.chat_message("user", avatar="🤖"):
                        res = agent.negotiate(chat_log)
                        st.write(f"**{agent.name}'s Assistant:** {res['message']}")
                        
                        chat_log += f"\n{agent.name}: {res['message']} (Proposal: {res['proposal']})"
                        
                        if res['status'] == "ACCEPT":
                            st.success(f"✅ FINAL PLAN: {res['proposal']}")
                            st.balloons()
                            st.stop()
                    time.sleep(0.5)
else:
    st.info("No one has joined the room yet. Share the link in the sidebar!")

