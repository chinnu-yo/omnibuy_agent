# System Architecture Specification

## 1. High-Level Architecture Diagram

┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend Client                         │
│                    (React 19 / Tailwind / Lucide)                      │
│                                                                        │
│   ┌──────────────────────────────┐    ┌────────────────────────────┐   │
│   │ Conversational & MCQ Chat UI │    │ Live Agent Thought Ledger  │   │
│   └──────────────┬───────────────┘    └─────────────▲──────────────┘   │
│                  │                                  │                  │
│                  │ (1) User Prompts / MCQ Select    │ (SSE/REST Trace) │
│                  ▼                                  │                  │
│   ┌─────────────────────────────────────────────────┴──────────────┐   │
│   │               Razorpay Standard Checkout SDK Modal             │   │
│   └──────────────────────────────┬─────────────────────────────────┘   │
└──────────────────────────────────┼─────────────────────────────────────┘
│ HTTP POST (REST)
▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend Engine                          │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                     Agent Reasoning Core                       │   │
│   │               (Google Gemini API / google-genai)               │   │
│   │   - Generates Dynamic Clarifying MCQs                          │   │
│   │   - Converts Intent to Live Product Queries                    │   │
│   └──────────────┬───────────────────────────────────▲─────────────┘   │
│                  │                                   │                 │
│                  ▼                                   │                 │
│   ┌──────────────────────────────┐                   │                 │
│   │   Live Web Harvester Tool    │                   │                 │
│   │     (duckduckgo-search)      │                   │                 │
│   └──────────────┬───────────────┘                   │                 │
│                  │                                   │                 │
│                  ▼                                   │                 │
│   ┌──────────────────────────────────────────────────┴─────────────┐   │
│   │           Deterministic Guardrail & Pydantic Engine            │   │
│   │   - Re-sums exact item prices (float)                          │   │
│   │   - Validates total_price <= budget_cap (Hard Assertion)       │   │
│   └──────────────┬─────────────────────────────────────────────────┘   │
│                  │                                                     │
│                  ▼                                                     │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                    Razorpay Python Service                     │   │
│   │   - razorpay.Client(auth=(KEY_ID, SECRET))                     │   │
│   │   - client.order.create(amount_in_paise)                       │   │
│   │   - client.utility.verify_payment_signature(...)               │   │
│   └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘


## 2. Core Operational Flow
1. **Discovery Turn:** User enters broad goal $\rightarrow$ Backend prompts Gemini with structured JSON output schema $\rightarrow$ Frontend renders dynamic MCQ choices.
2. **Sourcing Turn:** User answers MCQs $\rightarrow$ Backend decomposes intent into individual search terms $\rightarrow$ `duckduckgo-search` queries live marketplace listings.
3. **Guardrail Evaluation:** Backend parses extracted prices into Pydantic models, calculates $\sum \text{price}$, and verifies budget compliance.
4. **Order Generation:** Backend creates an order via `razorpay-python` (`amount * 100` paise).
5. **Client Settlement:** Frontend launches Razorpay Checkout popup $\rightarrow$ User submits test credentials.
6. **Cryptographic Settlement:** Frontend sends `{order_id, payment_id, signature}` to `/api/order/verify` $\rightarrow$ Backend confirms SHA-256 HMAC signature.