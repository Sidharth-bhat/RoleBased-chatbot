# Role-Based Chatbot System

Enterprise role-based chatbot with strict knowledge isolation, JWT authentication, semantic search (RAG), and output guardrails.

## Features

- **Auto-Classification** — maps raw leads CSV to roles (BUYER / CHANNEL_PARTNER / SITE_VISIT / UNKNOWN)
- **Multi-Agent System** — physically isolated knowledge bases per role
- **JWT Authentication** — secure, stateless role-based routing
- **Output Guardrails** — keyword-level cross-role data leakage prevention
- **Audit Logging** — immutable compliance trail per interaction
- **Full-Stack UI** — premium dark-mode chat interface served directly by Flask

## Stack

| Layer     | Technology                     |
|-----------|--------------------------------|
| Backend   | Python · Flask · Flask-CORS    |
| Auth      | PyJWT (HS256)                  |
| AI / RAG  | sentence-transformers (MiniLM) |
| Frontend  | HTML · Vanilla CSS · Vanilla JS|
| Data      | pandas · CSV                   |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Classify leads (generates data/classified_leads.csv)
python classification/classify_leads.py

# 3. Run the server
python chatbot/app.py
```

Then open **http://localhost:5000** in your browser.

## Demo Accounts

| Role             | Phone        |
|------------------|--------------|
| Buyer            | `7564209312` |
| Channel Partner  | `9105578047` |
| Site Visit       | `6941460145` |
| Unknown          | `6682751893` |

## API Endpoints

| Method | Endpoint      | Description                      |
|--------|---------------|----------------------------------|
| POST   | `/api/login`  | Authenticate → get JWT token     |
| POST   | `/api/chat`   | Send message (Bearer token auth) |
| GET    | `/api/audit`  | Fetch last 50 audit log entries  |
| GET    | `/api/status` | Health check                     |

## Architecture

```
User Login → JWT Token → API Gateway (ChatbotRouter)
                              │
               ┌──────────────┼──────────────┬──────────────┐
               ↓              ↓              ↓              ↓
          BuyerAgent    PartnerAgent   VisitorAgent   FallbackAgent
          buyer_kb.json partner_kb.json visitor_kb.json  (no KB)
               └──────────────┴──────────────┴──────────────┘
                                     │
                           Output Guardrails
                                     │
                            Audit Log Entry
                                     │
                             Response to User
```

## Security

✅ Zero cross-role data leakage  
✅ Physical knowledge base isolation  
✅ JWT-based stateless authentication  
✅ Input + output guardrails  
✅ Immutable audit logging  
