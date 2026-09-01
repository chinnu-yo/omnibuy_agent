# UI / UX Design Specification

## 1. Design System & Aesthetics
* **Theme:** Modern Fintech Terminal / Dark Mode (`bg-zinc-950`, `text-zinc-100`, accents in `emerald-500`, `blue-500`, and `violet-500`).
* **Typography:** Clean sans-serif (`Inter` or `Geist Sans`) with monospace (`JetBrains Mono` or `Fira Code`) for live tool logs, JSON payloads, and audit traces.

## 2. Layout Structure (Split-Screen Architecture)
The desktop view is strictly divided into two distinct functional panes:

### Left Pane: Conversational Commerce Interface (60% Width)
* **Header:** Agent status badge (`Online - Gemini 2.5 Flash`), active budget ceiling indicator, and session reset button.
* **Chat Message Thread:**
  * **User Bubble:** Right-aligned, minimal slate styling.
  * **Agent Bubble:** Left-aligned, markdown rendered.
  * **Interactive MCQ Card Component:** Renders dynamic options as clickable pill chips (`[A]`, `[B]`, `[C]`). When clicked, it disables the buttons and submits the selection seamlessly.
  * **Curated Bundle Card:** Displays the recommended items with title, live price (₹), source merchant badge (Amazon/Croma/Flipkart), and an **"Approve & Pay with Razorpay"** primary CTA button.

### Right Pane: Real-Time Agent Thought & Guardrail Ledger (40% Width)
* **Live Action Log:** Real-time visual cards displaying:
  * `[INTENT_PARSED]` Structured user requirements.
  * `[TOOL_INVOCATION]` Live DuckDuckGo queries sent to the web.
  * `[GUARDRAIL_ASSERTION]` Mathematical price sum validation vs. maximum budget limit.
  * `[RAZORPAY_STATE]` Order creation details (`order_id`, amount in paise, receipt hash).
  * `[CRYPTO_VERIFICATION]` HMAC SHA-256 signature verification status.

## 3. Modal & State Management
* **Razorpay Checkout Modal:** Invoked via Razorpay Standard Checkout JS (`https://checkout.razorpay.com/v1/checkout.js`).
* **Success State:** Confirmed transaction modal with green checkmark, payment ID, verified signature badge, and mock fulfillment dispatch tracker.
* **Failure/Recovery State:** Amber warning banner detailing the issue (e.g., *Item out of stock*) and the agent's autonomous recovery attempt.