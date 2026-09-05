import requests

API_BASE_URL = "http://127.0.0.1:8000"

print("1. Testing Initiate Chat for 'i need a smart phone and ear pods'...")
res1 = requests.post(f"{API_BASE_URL}/api/chat/initiate", json={
    "session_id": "test_phone_123",
    "message": "i need a smart phone and ear pods",
    "budget_cap": 18000,
    "user_selections": {}
})
data1 = res1.json()
print("Questions generated:")
for q in data1.get("questions", []):
    print(" -", q.get("question_text"))

print("\n2. Testing Recommend Bundle for 'i need a smart phone and ear pods'...")
res2 = requests.post(f"{API_BASE_URL}/api/chat/recommend", json={
    "session_id": "test_phone_123",
    "message": "i need a smart phone and ear pods",
    "budget_cap": 18000,
    "user_selections": {
        "q1": "Android 5G Smooth 120Hz",
        "q2": "Active Noise Cancellation (ANC)"
    }
})
data2 = res2.json()
bundle = data2.get("bundle", {})
print(f"Bundle Name: {bundle.get('bundle_name')}")
print(f"Total Price: Rs.{bundle.get('total_price')} (Within Budget: {bundle.get('is_within_budget')})")
print("Items in Bundle:")
for item in bundle.get("items", []):
    print(f" * [{item.get('category')}] {item.get('title')} - Rs.{item.get('price')} ({item.get('url')})")
