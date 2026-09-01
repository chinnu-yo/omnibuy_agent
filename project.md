# Project Specification: OmniBuyer Agent

## 1. Project Overview
* **Project Name:** OmniBuyer Agent
* **Target:** Razorpay AI Buildathon 2026 — Track 01: AI Growth & Agentic Commerce
* **Core Value Proposition:** An autonomous, category-agnostic buyer agent that conducts interactive conversational discovery (non-technical MCQs), scrapes live product listings from the open web, deterministically verifies budget ceilings and pricing (zero LLM math hallucination), and executes unified checkout via Razorpay Standard Checkout with local cryptographic HMAC SHA-256 verification.

## 2. Key Objectives & Winning Criteria
1. **Agentic Conversational Discovery:** Ask dynamic, category-relevant clarifying multiple-choice questions (MCQs) before searching.
2. **Dynamic Live Web Discovery:** Sourced in real time via live web search (`duckduckgo-search`), avoiding static or hardcoded merchant mock databases.
3. **Deterministic Guardrail Engine:** All mathematical operations (price summation, discount calculations, budget ceiling compliance) must be executed strictly by Python backend logic / Pydantic validators, never calculated via LLM prompt output.
4. **End-to-End Fintech Integration:** Programmatic creation of Razorpay Orders (`order_id`) and client-side modal invocation, followed by server-side payment signature verification.
5. **Self-Healing & Failure Recovery:** Catch out-of-stock items, price surges, or budget violations dynamically, autonomously swapping SKUs and re-presenting an updated valid cart.

## 3. Deliverables Checklist
- [ ] Public GitHub repository with clean modular architecture and complete `README.md`.
- [ ] Python FastAPI backend running locally on `http://localhost:8000`.
- [ ] Next.js (App Router) frontend running locally on `http://localhost:3000`.
- [ ] 5-Minute video demonstration showing happy-path checkout and graceful failure recovery.