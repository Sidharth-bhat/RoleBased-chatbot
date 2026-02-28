import json
import re
from typing import List, Dict

class KnowledgeBase:
    """Isolated knowledge base for each role"""
    def __init__(self, kb_path: str):
        with open(kb_path, 'r') as f:
            data = json.load(f)
        self.role = data['role']
        self.knowledge = data['knowledge']
    
    def search(self, query: str) -> List[Dict]:
        """Simple keyword-based search"""
        query_lower = query.lower()
        results = []
        
        # Search for matching topics
        for item in self.knowledge:
            topic_words = item['topic'].lower().split()
            if any(word in query_lower for word in topic_words):
                results.append(item)
        
        # If no match, search in content
        if not results:
            for item in self.knowledge:
                content_words = item['content'].lower().split()
                if any(word in query_lower for word in content_words[:10]):  # Check first 10 words
                    results.append(item)
        
        return results if results else []

class Agent:
    """Specialized agent with isolated knowledge access"""
    def __init__(self, role: str, kb_path: str, restricted_topics: List[str]):
        self.role = role
        self.kb = KnowledgeBase(kb_path)
        self.restricted_topics = restricted_topics
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        prompts = {
            "BUYER": "You are a specialized assistant for property buyers. Provide information about pricing, EMI, booking, and availability only.",
            "CHANNEL_PARTNER": "You are a specialized assistant for channel partners. Provide information about commissions, partnership terms, and referrals only.",
            "SITE_VISIT": "You are a specialized assistant for site visits. Provide information about location, scheduling, and directions only."
        }
        return prompts.get(self.role, "You are a general assistant.")
    
    def _check_guardrails(self, response: str) -> bool:
        """Output guardrail to prevent data leakage"""
        response_lower = response.lower()
        for topic in self.restricted_topics:
            if topic in response_lower:
                return False
        return True
    
    def respond(self, query: str) -> str:
        """Generate response with guardrails"""
        # Retrieve context from isolated KB
        context = self.kb.search(query)
        
        # Generate response (simplified - in production use LLM)
        if not context:
            response = f"I'm a specialized assistant for {self.role.replace('_', ' ').lower()}s. I can help you with relevant information. Please ask about topics related to my role."
        else:
            response = ""
            for item in context:
                response += f"**{item['topic'].title()}**: {item['content']}\n\n"
        
        # Apply guardrails
        if not self._check_guardrails(response):
            return "I cannot provide that information. Please contact a human representative."
        
        return response.strip()

class BuyerAgent(Agent):
    def __init__(self):
        super().__init__(
            role="BUYER",
            kb_path="chatbot/knowledge_bases/buyer_kb.json",
            restricted_topics=["commission", "referral", "partnership", "incentive"]
        )

class PartnerAgent(Agent):
    def __init__(self):
        super().__init__(
            role="CHANNEL_PARTNER",
            kb_path="chatbot/knowledge_bases/partner_kb.json",
            restricted_topics=["pricing", "emi", "booking", "buyer"]
        )

class VisitorAgent(Agent):
    def __init__(self):
        super().__init__(
            role="SITE_VISIT",
            kb_path="chatbot/knowledge_bases/visitor_kb.json",
            restricted_topics=["commission", "pricing", "emi", "booking"]
        )

class FallbackAgent:
    """Agent for unclassified users"""
    def respond(self, query: str) -> str:
        return """Welcome! I need to understand your requirement better.

Are you:
1. Looking to BUY a property?
2. A CHANNEL PARTNER interested in our partnership program?
3. Planning a SITE VISIT?

Please specify your interest so I can assist you better."""
