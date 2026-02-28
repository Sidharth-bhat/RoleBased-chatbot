import streamlit as st
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'chatbot'))
from chatbot.app import ChatbotRouter

# Page config
st.set_page_config(page_title="Role-Based Chatbot Demo", page_icon="🤖", layout="wide")

# Load users
@st.cache_data
def load_users():
    df = pd.read_csv('data/classified_leads.csv')
    return {str(row['Phone Number']): {"name": row['Name'], "role": row['Role']} 
            for _, row in df.iterrows()}

# Initialize
if 'router' not in st.session_state:
    st.session_state.router = ChatbotRouter()
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'messages' not in st.session_state:
    st.session_state.messages = []

users = load_users()

# Header
st.title("🤖 Role-Based Chatbot System")
st.markdown("**Enterprise-Grade Knowledge Isolation Demo**")

# Sidebar - Authentication
with st.sidebar:
    st.header("🔐 User Login")
    
    if not st.session_state.authenticated:
        phone = st.text_input("Phone Number", placeholder="7564209312")
        
        if st.button("Login", type="primary"):
            user = users.get(phone)
            if user:
                st.session_state.phone = phone
                st.session_state.user = user
                st.session_state.token = st.session_state.router.generate_jwt(phone, user['role'])
                st.session_state.authenticated = True
                st.session_state.messages = []
                st.rerun()
            else:
                st.error("❌ User not found. Try: 7564209312")
        
        st.divider()
        st.subheader("📋 Test Users")
        st.code("7564209312 - BUYER\n9105578047 - PARTNER\n6941460145 - SITE_VISIT\n6682751893 - UNKNOWN")
    
    else:
        st.success(f"✅ Logged in as **{st.session_state.user['name']}**")
        st.info(f"**Role:** {st.session_state.user['role']}")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        st.subheader("🧪 Test Queries")
        
        if st.session_state.user['role'] == 'BUYER':
            st.markdown("**✅ Try:**\n- What is the price?\n- EMI options?\n\n**❌ Try (blocked):**\n- Commission structure?")
        elif st.session_state.user['role'] == 'CHANNEL_PARTNER':
            st.markdown("**✅ Try:**\n- Commission rates?\n- Referral policy?\n\n**❌ Try (blocked):**\n- Apartment prices?")
        elif st.session_state.user['role'] == 'SITE_VISIT':
            st.markdown("**✅ Try:**\n- Where is location?\n- Visit timings?\n\n**❌ Try (blocked):**\n- Commission details?")

# Main chat area
if not st.session_state.authenticated:
    st.info("👈 Please login with a phone number to start chatting")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", len(users))
    with col2:
        st.metric("Roles", "4")
    with col3:
        st.metric("Guardrails", "Active")
    
    st.divider()
    st.subheader("🎯 System Features")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **✅ Security:**
        - JWT-based authentication
        - Physical KB isolation
        - Output guardrails
        - Audit logging
        """)
    with col2:
        st.markdown("""
        **✅ Architecture:**
        - Multi-agent system
        - Network-level routing
        - Zero cross-role leakage
        - Fallback handling
        """)

else:
    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("guardrail"):
                st.warning("🛡️ Guardrail triggered - Cross-role data blocked")
    
    # Chat input
    if prompt := st.chat_input("Ask a question..."):
        # User message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Bot response
        response = st.session_state.router.route_user(st.session_state.token, prompt)
        guardrail_triggered = "cannot provide that information" in response.lower()
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "guardrail": guardrail_triggered
        })
        
        with st.chat_message("assistant"):
            st.markdown(response)
            if guardrail_triggered:
                st.warning("🛡️ Guardrail triggered - Cross-role data blocked")
        
        st.rerun()

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Interactions", len(st.session_state.router.audit_log))
with col2:
    if st.session_state.authenticated:
        st.metric("Current Role", st.session_state.user['role'])
with col3:
    st.metric("Status", "🟢 Active")
