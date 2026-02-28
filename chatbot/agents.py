import json
import re
import os
from typing import List, Dict

class KnowledgeBase:
    """Isolated knowledge base for each role"""
    def __init__(self, kb_path: str):
        try:
            with open(kb_path, 'r') as f:
                data = json.load(f)
            self.role = data.get('role', 'UNKNOWN')
            self.knowledge = data.get('knowledge', [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load KB at {kb_path}: {e}")
            self.role = "UNKNOWN"
            self.knowledge = []
    
    def search(self, query: str) -> List[Dict]:
        """Simple keyword-based search"""
        # Remove punctuation and convert to lower case
        query_clean = re.sub(r'[^\w\s]', '', query.lower())
        query_tokens = query_clean.split()
        
        # Filter significant words (len > 3)
        significant_words = [w for w in query_tokens if len(w) > 3]
        
        results = []
        
        # Search for matching topics
        for item in self.knowledge:
            topic_lower = item['topic'].lower()
            
            # 1. Exact word match for topic in query
            if re.search(r'\b' + re.escape(topic_lower) + r'\b', query_clean):
                results.append(item)
                continue
                
            # 2. Partial match: significant query word inside topic (e.g. "price" in "pricing")
            if any(word in topic_lower for word in significant_words):
                results.append(item)
                continue
        
        # If no match, search in content
        if not results and significant_words:
            for item in self.knowledge:
                content_lower = item['content'].lower()
                if any(word in content_lower for word in significant_words):
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
        # 1. Retrieve context (RAG Pattern - Retrieval)
        context = self.kb.search(query)
        
        # 2. Generate response (RAG Pattern - Generation)
        # Currently using deterministic logic. In production, replace _generate_deterministic 
        # with an LLM call (e.g., OpenAI GPT-4) passing the context and system_prompt.
        response = self._generate_deterministic(context)
        
        # 3. Apply guardrails (Safety)
        if not self._check_guardrails(response):
            return "I cannot provide that information. Please contact a human representative."
        
        return response.strip()

    def _generate_deterministic(self, context: List[Dict]) -> str:
        """Simulates LLM generation using static templates"""
        if not context:
            return f"I apologize, but I don't have access to that information. As a {self.role.replace('_', ' ').title()}, I can only assist you with topics relevant to your role.If any query please contact adminstator@edu"
            return f"I apologize, but I don't have access to that information. As a {self.role.replace('_', ' ').title()}, I can only assist you with topics relevant to your role. If you have any queries, please contact administrator@edu."
        
        response = ""
        for item in context:
            response += f"**{item['topic'].title()}**: {item['content']}\n\n"
        return response

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
