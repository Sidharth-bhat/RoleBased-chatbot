"""
Role-based agent system with isolated knowledge bases and guardrails.

Performance note: KB topic/content embeddings are pre-computed once at
init time rather than on every query — makes semantic search ~50x faster.
"""
import json
import os
from typing import List, Dict

from sentence_transformers import SentenceTransformer, util

from config import cfg


# ── Knowledge Base ─────────────────────────────────────────────────────────────

class KnowledgeBase:
    """Isolated knowledge base for a single role."""

    _model: SentenceTransformer = None  # shared singleton across all KBs

    @classmethod
    def _get_model(cls) -> SentenceTransformer:
        if cls._model is None:
            print(f"🔄 Loading embedding model ({cfg.EMBEDDING_MODEL})...")
            cls._model = SentenceTransformer(cfg.EMBEDDING_MODEL)
            print("✅ Embedding model loaded.")
        return cls._model

    def __init__(self, kb_path: str):
        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.role      = data.get("role", "UNKNOWN")
            self.knowledge = data.get("knowledge", [])

            # Pre-compute embeddings for all topics and content once at startup
            model = self._get_model()
            self._topic_embeddings   = [model.encode(item["topic"],   convert_to_tensor=True) for item in self.knowledge]
            self._content_embeddings = [model.encode(item["content"], convert_to_tensor=True) for item in self.knowledge]

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️  Could not load KB at {kb_path}: {e}")
            self.role      = "UNKNOWN"
            self.knowledge = []
            self._topic_embeddings   = []
            self._content_embeddings = []

    def search(self, query: str, min_score: float = None, top_k: int = None) -> List[Dict]:
        """
        Semantic search using pre-computed embeddings.
        Returns top-k results above min_score threshold, sorted by score desc.
        """
        if not self.knowledge:
            return []

        min_score = min_score if min_score is not None else cfg.KB_MIN_SCORE
        top_k     = top_k     if top_k     is not None else cfg.KB_TOP_K

        model = self._get_model()
        query_embedding = model.encode(query, convert_to_tensor=True)

        results = []
        for i, item in enumerate(self.knowledge):
            topic_score   = util.pytorch_cos_sim(query_embedding, self._topic_embeddings[i]).item()
            content_score = util.pytorch_cos_sim(query_embedding, self._content_embeddings[i]).item()
            score = max(topic_score, content_score)

            if score >= min_score:
                results.append({**item, "similarity": round(score, 4)})

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]


# ── Base Agent ─────────────────────────────────────────────────────────────────

class Agent:
    """Specialized agent with isolated KB access and tiered guardrails."""

    SYSTEM_PROMPTS = {
        "BUYER":
            "You are a specialized assistant for property buyers. "
            "Provide information about pricing, EMI, booking, and availability only.",
        "CHANNEL_PARTNER":
            "You are a specialized assistant for channel partners. "
            "Provide information about commissions, partnership terms, and referrals only.",
        "SITE_VISIT":
            "You are a specialized assistant for site visits. "
            "Provide information about location, scheduling, and directions only.",
    }

    def __init__(self, role: str, kb_path: str, restricted_topics: List[str]):
        self.role              = role
        self.kb                = KnowledgeBase(kb_path)
        self.restricted_topics = [t.lower() for t in restricted_topics]
        self.system_prompt     = self.SYSTEM_PROMPTS.get(role, "You are a general assistant.")

    # ── Guardrails ─────────────────────────────────────────────────────────────

    def _contains_restricted(self, text: str) -> bool:
        text_lower = text.lower()
        return any(topic in text_lower for topic in self.restricted_topics)

    # ── Response pipeline ──────────────────────────────────────────────────────

    def respond(self, query: str) -> str:
        """
        Full pipeline:
          1. Input guardrail
          2. KB retrieval  (RAG — Retrieve)
          3. Response generation (RAG — Generate)
          4. Output guardrail
        """
        # 1. Input guardrail
        if self._contains_restricted(query):
            return (
                "I apologize, but I cannot provide information regarding that topic. "
                f"As a {self.role.replace('_', ' ').title()} assistant, I can only help "
                "with queries relevant to your role."
            )

        # 2. Retrieve
        context = self.kb.search(query)

        # 3. Generate
        response = self._generate(context)

        # 4. Output guardrail
        if self._contains_restricted(response):
            return "I cannot provide that information. Please contact a human representative."

        return response.strip()

    def _generate(self, context: List[Dict]) -> str:
        """
        Deterministic template-based generation from retrieved KB entries.
        In production: replace with an LLM call using self.system_prompt + context.
        """
        if not context:
            return (
                f"I don't have specific information on that topic. "
                f"As a {self.role.replace('_', ' ').title()} assistant, I can help with: "
                + ", ".join(item["topic"].title() for item in self.kb.knowledge[:5])
                + ". Please try rephrasing your question."
            )

        parts = []
        for item in context:
            parts.append(f"**{item['topic'].title()}**: {item['content']}")
        return "\n\n".join(parts)


# ── Concrete Agents ────────────────────────────────────────────────────────────

class BuyerAgent(Agent):
    def __init__(self):
        super().__init__(
            role="BUYER",
            kb_path=os.path.join(cfg.KB_DIR, "buyer_kb.json"),
            restricted_topics=["commission", "referral", "partnership", "incentive"],
        )


class PartnerAgent(Agent):
    def __init__(self):
        super().__init__(
            role="CHANNEL_PARTNER",
            kb_path=os.path.join(cfg.KB_DIR, "partner_kb.json"),
            restricted_topics=["price", "emi", "booking", "buyer"],
        )


class VisitorAgent(Agent):
    def __init__(self):
        super().__init__(
            role="SITE_VISIT",
            kb_path=os.path.join(cfg.KB_DIR, "visitor_kb.json"),
            restricted_topics=["commission", "pricing", "emi", "booking"],
        )


class FallbackAgent:
    """Agent for unclassified / unknown users."""

    role = "UNKNOWN"

    def respond(self, query: str) -> str:  # noqa: ARG002
        return (
            "Welcome! I need to understand your requirement better.\n\n"
            "Are you:\n"
            "1. Looking to **BUY** a property?\n"
            "2. A **CHANNEL PARTNER** interested in our partnership program?\n"
            "3. Planning a **SITE VISIT**?\n\n"
            "Please specify your interest so I can connect you to the right assistant."
        )
