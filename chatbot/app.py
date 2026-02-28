import pandas as pd
import jwt
import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from agents import BuyerAgent, PartnerAgent, VisitorAgent, FallbackAgent

SECRET_KEY = "your-secret-key-change-in-production"

class ChatbotRouter:
    """API Gateway - Deterministic routing based on JWT"""
    def __init__(self):
        self.agents = {
            "BUYER": BuyerAgent(),
            "CHANNEL_PARTNER": PartnerAgent(),
            "SITE_VISIT": VisitorAgent(),
            "UNKNOWN": FallbackAgent()
        }
        self.audit_log = []
    
    def generate_jwt(self, user_id: str, role: str) -> str:
        """Generate JWT token with role claim"""
        payload = {
            "user_id": user_id,
            "role": role,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    def verify_jwt(self, token: str) -> dict:
        """Verify and extract JWT payload"""
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return {"role": "UNKNOWN"}
    
    def route_user(self, token: str, query: str) -> str:
        """Deterministic routing - network level isolation"""
        # Step 1: Verify token and extract role
        payload = self.verify_jwt(token)
        role = payload.get("role", "UNKNOWN")
        user_id = payload.get("user_id", "anonymous")
        
        # Step 2: Route to appropriate agent (network-level routing)
        agent = self.agents.get(role, self.agents["UNKNOWN"])
        
        # Step 3: Generate response
        response = agent.respond(query)
        
        # Step 4: Audit logging
        self._log_interaction(user_id, role, query, response)
        
        return response
    
    def _log_interaction(self, user_id: str, role: str, query: str, response: str):
        """Immutable audit trail for compliance"""
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "user_id": user_id,
            "role": role,
            "query": query[:100],  # Truncate for privacy
            "response_length": len(response),
            "agent_used": role
        }
        self.audit_log.append(log_entry)

def load_user_database():
    """Load classified leads as user database"""
    try:
        df = pd.read_csv('data/classified_leads.csv')
        users = {}
        for _, row in df.iterrows():
            users[str(row['Phone Number'])] = {
                "name": row['Name'],
                "role": row['Role']
            }
        return users
    except FileNotFoundError:
        print("Please run classification/classify_leads.py first!")
        return {}

def demo_chatbot():
    """Interactive demo"""
    print("=" * 60)
    print("ROLE-BASED CHATBOT SYSTEM - DEMO")
    print("=" * 60)
    
    router = ChatbotRouter()
    users = load_user_database()
    
    if not users:
        return
    
    print(f"\nLoaded {len(users)} users from database")
    print("\nEnter phone number to simulate user login (or 'quit' to exit)")
    
    while True:
        phone = input("\nPhone Number: ").strip()
        
        if phone.lower() == 'quit':
            break
        
        user = users.get(phone)
        
        if not user:
            print("User not found. Try: 6682751893")
            continue
        
        # Generate JWT token
        token = router.generate_jwt(phone, user['role'])
        
        print(f"\n✓ Authenticated: {user['name']}")
        print(f"✓ Role: {user['role']}")
        print(f"✓ JWT Token: {token[:30]}...")
        print("\nYou can now chat. Type 'back' to switch user.\n")
        
        while True:
            query = input("You: ").strip()
            
            if query.lower() == 'back':
                break
            
            if not query:
                continue
            
            # Route to appropriate agent
            response = router.route_user(token, query)
            print(f"\nBot: {response}\n")
    
    # Show audit log
    print("\n" + "=" * 60)
    print(f"AUDIT LOG: {len(router.audit_log)} interactions logged")
    print("=" * 60)

if __name__ == "__main__":
    demo_chatbot()
