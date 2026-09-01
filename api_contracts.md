# API Contracts & Data Schemas

## Base URL: `http://127.0.0.1:8000`

---

### 1. Initiate Discovery (Generate MCQs)
* **Endpoint:** `POST /api/chat/initiate`
* **Request Body:**
```json
{
  "session_id": "sess_abc123",
  "message": "I need a full competitive FPS gaming setup",
  "budget_cap": 8000.0,
  "user_selections": {}
}
Response (200 OK):

JSON
{
  "status": "clarifying",
  "questions": [
    {
      "question_id": "q1",
      "question_text": "What type of keyboard switch do you prefer?",
      "options": [
        {"id": "opt_red", "label": "Linear Red", "description": "Quiet and fast for competitive gaming"},
        {"id": "opt_blue", "label": "Clicky Blue", "description": "Tactile feedback and audible click"},
        {"id": "opt_brown", "label": "Tactile Brown", "description": "Balanced feel for typing and gaming"}
      ]
    },
    {
      "question_id": "q2",
      "question_text": "Do you need a wired or wireless mouse?",
      "options": [
        {"id": "opt_ultralight_wired", "label": "Ultralight Wired", "description": "Zero latency, lowest weight"},
        {"id": "opt_wireless", "label": "2.4GHz Wireless", "description": "Clean desk setup with rechargeable battery"}
      ]
    }
  ]
}
2. Recommend Bundle (Live Sourced & Validated)
Endpoint: POST /api/chat/recommend

Request Body:

JSON
{
  "session_id": "sess_abc123",
  "message": "I need a full competitive FPS gaming setup",
  "budget_cap": 8000.0,
  "user_selections": {
    "q1": "Linear Red",
    "q2": "Ultralight Wired"
  }
}
Response (200 OK):

JSON
{
  "status": "ready",
  "bundle": {
    "bundle_name": "Curated Competitive FPS Gaming Setup",
    "items": [
      {
        "title": "Cosmic Byte CB-GK-16 Firefly RGB Mechanical Keyboard (Red Switches)",
        "price": 2199.0,
        "source": "Amazon",
        "url": "[https://amazon.in/dp/example1](https://amazon.in/dp/example1)",
        "category": "mechanical keyboard"
      },
      {
        "title": "Razer DeathAdder Essential Gaming Mouse (6400 DPI)",
        "price": 1449.0,
        "source": "Amazon",
        "url": "[https://amazon.in/dp/example2](https://amazon.in/dp/example2)",
        "category": "gaming mouse"
      },
      {
        "title": "SpinBot Armor Extended Speed Type Gaming Mouse Pad (900x400mm)",
        "price": 599.0,
        "source": "Amazon",
        "url": "[https://amazon.in/dp/example3](https://amazon.in/dp/example3)",
        "category": "desk mat"
      }
    ],
    "total_price": 4247.0,
    "budget_cap": 8000.0,
    "is_within_budget": true
  }
}
3. Create Razorpay Order
Endpoint: POST /api/order/create

Request Body:

JSON
{
  "bundle": {
    "bundle_name": "Curated Competitive FPS Gaming Setup",
    "items": [ ... ],
    "total_price": 4247.0,
    "budget_cap": 8000.0,
    "is_within_budget": true
  }
}
Response (200 OK):

JSON
{
  "order": {
    "id": "order_P1q8zY9xXw3AbC",
    "amount": 424700,
    "currency": "INR",
    "status": "created"
  },
  "key_id": "rzp_test_placeholder"
}
4. Verify Payment Signature
Endpoint: POST /api/order/verify

Request Body:

JSON
{
  "razorpay_order_id": "order_P1q8zY9xXw3AbC",
  "razorpay_payment_id": "pay_P1q9ABC12345",
  "razorpay_signature": "9a8f7c6e5d4b3a210fedcba987654321..."
}
Response (200 OK):

JSON
{
  "status": "SUCCESS",
  "message": "Payment verified. Mock dispatch triggered."
}