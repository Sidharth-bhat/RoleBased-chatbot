"""
Automated Test Script - Demonstrates Role-Based Isolation
"""
from chatbot.app import ChatbotRouter, load_user_database

def test_isolation():
    print("=" * 70)
    print("AUTOMATED TEST: ROLE-BASED ISOLATION & GUARDRAILS")
    print("=" * 70)
    
    router = ChatbotRouter()
    users = load_user_database()
    
    # Test cases
    test_cases = [
        {
            "phone": "7564209312",  # Buyer
            "queries": [
                "What is the price?",
                "Tell me about commission structure"  # Should be blocked
            ]
        },
        {
            "phone": "9105578047",  # Channel Partner
            "queries": [
                "What is my commission?",
                "What are the apartment prices?"  # Should be blocked
            ]
        },
        {
            "phone": "6941460145",  # Site Visit
            "queries": [
                "Where is the location?",
                "What is the commission?"  # Should be blocked
            ]
        },
        {
            "phone": "6682751893",  # Enquiry (UNKNOWN)
            "queries": [
                "I need help"
            ]
        }
    ]
    
    for test in test_cases:
        phone = test["phone"]
        user = users.get(phone)
        
        if not user:
            continue
        
        print(f"\n{'=' * 70}")
        print(f"TEST USER: {user['name']} | Role: {user['role']}")
        print("=" * 70)
        
        token = router.generate_jwt(phone, user['role'])
        
        for query in test["queries"]:
            print(f"\nQuery: {query}")
            response = router.route_user(token, query)
            print(f"Response: {response[:200]}...")
            
            # Check if guardrail triggered
            if "cannot provide that information" in response.lower():
                print("[GUARDRAIL TRIGGERED] Cross-role data blocked!")
    
    print(f"\n{'=' * 70}")
    print(f"AUDIT LOG: {len(router.audit_log)} interactions logged")
    print("=" * 70)
    
    # Show sample audit log
    if router.audit_log:
        print("\nSample Audit Entry:")
        import json
        print(json.dumps(router.audit_log[0], indent=2))

if __name__ == "__main__":
    test_isolation()
