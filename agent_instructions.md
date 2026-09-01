# Antigravity Agent Coding Instructions & Guardrails

## 1. Primary Directives
You are building the **OmniBuyer Agent** project. You must strictly adhere to the following constraints during all file generation and editing:

* **Zero Financial Hallucinations:** NEVER allow LLM prompt responses to compute, guess, or format final transaction totals. All arithmetic operations MUST be computed in Python using native numeric types and validated by Pydantic models.
* **No Mocking of Core Verification Logic:** Always invoke the actual `razorpay` Python SDK utility method `client.utility.verify_payment_signature()` for signature validation. If running in local mock test mode without real API keys, handle it via explicit environment flag checks (`MOCK_PAYMENT_MODE=true`), keeping the real verification path intact.
* **Strict CORS & Port Standards:**
  * Backend: FastAPI on `http://127.0.0.1:8000`
  * Frontend: Next.js on `http://localhost:3000`
  * CORS middleware must explicitly allow `http://localhost:3000` with all standard HTTP methods.

## 2. Coding Patterns
* **FastAPI:** Use typed Pydantic models for all request/response bodies. Do not accept untyped `dict` payloads in route handlers.
* **Gemini SDK:** Use the official `google-genai` SDK with structured JSON output configs (`response_mime_type="application/json"`).
* **Next.js:** Use the React 19 App Router (`app/page.tsx`). Keep state well-organized with clean React hooks (`useState`, `useEffect`, `useCallback`). Ensure Razorpay standard checkout script loads dynamically and safely.

## 3. Self-Correction & Failure Scenarios
* If DuckDuckGo returns empty search lists, the `search_service.py` must fall back to a curated set of standard pricing estimates without crashing the pipeline.
* If a generated bundle exceeds the user's budget ceiling, the backend must flag `is_within_budget = False` and block order creation with HTTP 400.