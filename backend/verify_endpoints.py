import urllib.request
import json
import sys
import hmac
import hashlib

BASE_URL = "http://127.0.0.1:8000"

def post_json(path, payload):
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def test_all():
    print("Testing Backend Live Endpoints at http://127.0.0.1:8000...")
    
    # 1. Healthcheck
    with urllib.request.urlopen(f"{BASE_URL}/health") as resp:
        health_data = json.loads(resp.read().decode('utf-8'))
        print("1. Healthcheck:", health_data)
        assert health_data["status"] == "healthy"

    # 2. Initiate Chat
    init_res = post_json("/api/chat/initiate", {
        "session_id": "sess_test",
        "message": "I need a competitive FPS gaming setup",
        "budget_cap": 8000.0,
        "user_selections": {}
    })
    print("\n2. Initiate Chat Response:")
    print(f"   Status: {init_res['status']}")
    print(f"   Questions Count: {len(init_res['questions'])}")
    assert len(init_res["questions"]) == 2

    # 3. Recommend Bundle
    rec_res = post_json("/api/chat/recommend", {
        "session_id": "sess_test",
        "message": "I need a competitive FPS gaming setup",
        "budget_cap": 8000.0,
        "user_selections": {"q1": "Linear Red", "q2": "Ultralight Wired"}
    })
    print("\n3. Recommend Bundle Response:")
    bundle = rec_res["bundle"]
    print(f"   Bundle Name: {bundle['bundle_name']}")
    print(f"   Items Count: {len(bundle['items'])}")
    print(f"   Total Price: Rs.{bundle['total_price']} (Within Budget: {bundle['is_within_budget']})")
    assert bundle["total_price"] > 0

    # 4. Create Order
    order_res = post_json("/api/order/create", {"bundle": bundle})
    print("\n4. Create Order Response:")
    order = order_res["order"]
    print(f"   Order ID: {order['id']}")
    print(f"   Amount in Paise: {order['amount']}")
    assert order["id"] and order["amount"] > 0

    # 5. Verify Order (computing valid HMAC SHA-256 test signature)
    key_secret = b"0zi5yUKfGbLuM8hWnJuJB5W0"
    payment_id = "pay_test_12345678"
    msg = f"{order['id']}|{payment_id}".encode('utf-8')
    valid_signature = hmac.new(key_secret, msg, hashlib.sha256).hexdigest()

    verify_res = post_json("/api/order/verify", {
        "razorpay_order_id": order["id"],
        "razorpay_payment_id": payment_id,
        "razorpay_signature": valid_signature
    })
    print("\n5. Verify Payment Response:")
    print(f"   Status: {verify_res['status']}")
    print(f"   Message: {verify_res['message']}")
    assert verify_res["status"] == "SUCCESS"

    print("\n[SUCCESS] ALL BACKEND ENDPOINTS ARE 100% OPERATIONAL!\n")

if __name__ == "__main__":
    try:
        test_all()
    except Exception as e:
        print(f"[ERROR] Error testing endpoints: {e}")
        sys.exit(1)
