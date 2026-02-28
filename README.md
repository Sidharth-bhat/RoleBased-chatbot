# Role-Based Chatbot System

Enterprise role-based automation and chatbot with strict knowledge isolation.

## Features

- **Auto-Classification**: XLOOKUP-based lead classification
- **Multi-Agent System**: Physical knowledge base isolation
- **JWT Authentication**: Secure role-based routing
- **Output Guardrails**: Prevents cross-role data leakage
- **Audit Logging**: Immutable compliance trail

## Quick Start

```bash
# Install dependencies
pip install pandas PyJWT streamlit

# Classify leads
python classification/classify_leads.py

# Run web demo
streamlit run streamlit_app.py
```

## Demo

Test with these phone numbers:
- `7564209312` - BUYER
- `9105578047` - CHANNEL_PARTNER
- `6941460145` - SITE_VISIT
- `6682751893` - UNKNOWN

## Architecture

```
User Login → JWT Token → API Gateway → Role-Based Agent → Isolated KB → Guardrails → Response
```
## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAW LEAD SOURCES                            │
│              (CSV, Web Forms, CRM Systems)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              CLASSIFICATION ENGINE                              │
│  • Data Sanitization (CLEAN, TRIM)                             │
│  • Mapping Table Lookup (XLOOKUP)                              │
│  • Role Assignment (BUYER/PARTNER/VISITOR/UNKNOWN)             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                 CENTRAL USER DATABASE                           │
│            (Stores: User ID, Name, Phone, Role)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              IDENTITY PROVIDER (JWT Generator)                  │
│         Generates Token: {user_id, role, expiry}               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                   API GATEWAY / ROUTER                          │
│  • Validates JWT Signature                                     │
│  • Extracts Role Claim                                         │
│  • Deterministic Network Routing                               │
└──────┬──────────────┬──────────────┬──────────────┬────────────┘
       │              │              │              │
       ↓              ↓              ↓              ↓
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  BUYER   │   │ PARTNER  │   │ VISITOR  │   │ FALLBACK │
│  AGENT   │   │  AGENT   │   │  AGENT   │   │  AGENT   │
│ (LLM-A)  │   │ (LLM-B)  │   │ (LLM-C)  │   │ (No LLM) │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │
     ↓              ↓              ↓              ↓
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ BUYER KB │   │PARTNER KB│   │VISITOR KB│   │  NO KB   │
│ • Pricing│   │•Commission│   │•Location │   │  ACCESS  │
│ • EMI    │   │•Referrals│   │•Schedule │   │          │
│ • Booking│   │•Terms    │   │•Directions│   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│            OUTPUT GUARDRAIL EVALUATOR                           │
│  • Keyword Filtering (commission, pricing, etc.)               │
│  • LLM-as-a-Judge Validation                                   │
│  • Block & Log Security Events                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              IMMUTABLE AUDIT LOGGING                            │
│  • Timestamp, User, Role, Query, Response                      │
│  • JWT Claims, Agent Used                                      │
│  • Compliance & Forensic Trail                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security

✅ Zero cross-role data leakage  
✅ Physical database isolation  
✅ Network-level routing  
✅ Output guardrails  
✅ Audit logging
