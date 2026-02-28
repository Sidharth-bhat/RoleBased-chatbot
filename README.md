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

## Security

✅ Zero cross-role data leakage  
✅ Physical database isolation  
✅ Network-level routing  
✅ Output guardrails  
✅ Audit logging
