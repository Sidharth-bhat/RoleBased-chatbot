import streamlit as st
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'chatbot'))
from chatbot.app import ChatbotRouter

# Page config
st.set_page_config(page_title="Role-Based Chatbot", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for cleaner UI
st.markdown("""
<style>
    .stButton button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

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

# Sidebar - Authentication
with st.sidebar:
    st.title("🔐 Access Portal")
    
    if not st.session_state.authenticated:
        st.markdown("### Login")
        phone = st.text_input("Phone Number", placeholder="e.g. 7564209312")
        
        if st.button("Login", type="primary", use_container_width=True):
            user = users.get(phone)
            if user:
                st.session_state.phone = phone
                st.session_state.user = user
                st.session_state.token = st.session_state.router.generate_jwt(phone, user['role'])
                st.session_state.authenticated = True
                st.session_state.messages = []
                st.rerun()
            else:
                st.error("User not found. Try: 7564209312")
        
        st.markdown("---")
        with st.expander("📋 **Test Credentials**", expanded=True):
            st.markdown("""
            | Role | Phone |
            |---|---|
            | **Buyer** | `7564209312` |
            | **Partner** | `9105578047` |
            | **Visitor** | `6941460145` |
            | **Unknown** | `6682751893` |
            """)
    
    else:
        st.success(f"👤 **{st.session_state.user['name']}**")
        st.caption(f"Role: **{st.session_state.user['role']}**")
        
        if st.button("Logout", type="secondary", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Session Stats")
        st.metric("Interactions", len(st.session_state.router.audit_log))
        
        st.markdown("### 💡 Suggested Queries")
        
        if st.session_state.user['role'] == 'BUYER':
            st.info("Try: Price, EMI, Availability")
            st.error("Blocked: Commission, Partnership")
        elif st.session_state.user['role'] == 'CHANNEL_PARTNER':
            st.info("Try: Commission, Referral policy")
            st.error("Blocked: Apartment prices")
        elif st.session_state.user['role'] == 'SITE_VISIT':
            st.info("Try: Location, Visit timings")
            st.error("Blocked: Commission details")

# Main chat area
if not st.session_state.authenticated:
    st.title("🤖 Enterprise AI Assistant")
    st.markdown("#### Secure, Role-Based Conversational Agent")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Users", len(users))
    col2.metric("Defined Roles", "4")
    col3.metric("System Status", "🟢 Online")
    
    st.markdown("### System Architecture")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**🛡️ Security Layer**\n\n- JWT-based stateless authentication\n- Physical Knowledge Base isolation\n- Output guardrails & sanitization")
    with col2:
        st.success("**🧠 Intelligence Layer**\n\n- Deterministic routing strategy\n- Role-specific context injection\n- Audit logging for compliance")

else:
    st.title("💬 Secure Chat Interface")
    
    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("guardrail"):
                st.warning("🛡️ **Guardrail Triggered**: Cross-role data access blocked.")
    
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
                st.warning("🛡️ **Guardrail Triggered**: Cross-role data access blocked.")
        
        st.rerun()
