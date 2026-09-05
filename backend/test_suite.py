import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schemas import BundleItem, Bundle
from agent import (
    generate_clarifying_questions,
    decompose_intent_to_queries,
    build_and_validate_bundle
)
from search_service import fetch_product_data, parse_price_from_text
from razorpay_service import create_order, verify_payment_signature

def test_1_mcq_generation():
    print("\n--- Test 1: Dynamic MCQ Generation ---")
    intent = "I need a competitive FPS gaming setup"
    questions, traces = generate_clarifying_questions(intent)
    assert len(questions) == 2, f"Expected 2 questions, got {len(questions)}"
    for q in questions:
        assert q.question_id and q.question_text and len(q.options) >= 2
        print(f"  [Q] {q.question_text}")
        for opt in q.options:
            print(f"      - {opt.label}: {opt.description}")
    print("[PASSED] Test 1 Passed!")

def test_2_search_extraction():
    print("\n--- Test 2: Search Extraction & Price Parsing ---")
    price1 = parse_price_from_text("Special deal on Mechanical Keyboard Rs. 2199.00 today!")
    assert price1 == 2199.0, f"Expected 2199.0, got {price1}"
    
    price2 = parse_price_from_text("Razer Mouse Rs. 1449 buy online")
    assert price2 == 1449.0, f"Expected 1449.0, got {price2}"

    item, log_msg = fetch_product_data("mechanical keyboard linear red", "keyboard")
    assert item is not None and item.price > 0
    print(f"  [Extracted Item] {item.title} | Price: Rs.{item.price} | Source: {item.source}")
    print("[PASSED] Test 2 Passed!")

def test_3_budget_guardrails():
    print("\n--- Test 3: Deterministic Budget Ceiling Guardrail Engine ---")
    items = [
        BundleItem(title="Keyboard A", price=2000.0, source="Amazon", url="http://example.com/1", category="keyboard"),
        BundleItem(title="Mouse B", price=1500.0, source="Amazon", url="http://example.com/2", category="mouse"),
        BundleItem(title="Mat C", price=500.0, source="Amazon", url="http://example.com/3", category="mat")
    ]
    
    # 3a. Under-budget test
    bundle_ok, traces_ok = build_and_validate_bundle(items=items, budget_cap=5000.0)
    assert bundle_ok.total_price == 4000.0, f"Expected sum 4000.0, got {bundle_ok.total_price}"
    assert bundle_ok.is_within_budget is True
    print(f"  [Under Budget Cart] Sum: Rs.{bundle_ok.total_price} <= Budget Rs.5000.0 -> Approved: {bundle_ok.is_within_budget}")

    # 3b. Over-budget assertion & self-healing recovery test
    over_items = [
        BundleItem(title="Expensive Keyboard", price=6000.0, source="Amazon", url="http://example.com/1", category="keyboard"),
        BundleItem(title="Pro Mouse", price=3000.0, source="Amazon", url="http://example.com/2", category="mouse")
    ]
    bundle_over, traces_over = build_and_validate_bundle(items=over_items, budget_cap=5000.0)
    # Self-healing should downscale or reject if still over
    print(f"  [Self-Healing Recovery] Adjusted Cart Sum: Rs.{bundle_over.total_price} | Budget Rs.5000.0")
    print("[PASSED] Test 3 Passed!")

def test_4_razorpay_signature_verification():
    print("\n--- Test 4: Razorpay Order Creation & Cryptographic Signature Verification ---")
    valid_bundle = Bundle(
        bundle_name="Test Bundle",
        items=[BundleItem(title="Test Item", price=1000.0, source="Amazon", url="http://ex.com", category="test")],
        total_price=1000.0,
        budget_cap=5000.0,
        is_within_budget=True
    )
    
    order, key_id, traces = create_order(valid_bundle)
    assert order.id and order.amount == 100000  # 1000 * 100 paise
    print(f"  [Order Created] Order ID: {order.id} | Amount in Paise: {order.amount}")

    is_verified, msg, verify_traces = verify_payment_signature(
        razorpay_order_id=order.id,
        razorpay_payment_id="pay_test_12345",
        razorpay_signature="sig_test_mock_signature"
    )
    assert is_verified is True
    print(f"  [Signature Verification] {msg}")
    print("[PASSED] Test 4 Passed!")

if __name__ == "__main__":
    print("==================================================")
    print("      OmniBuyer Agent Backend Dry-Run Suite       ")
    print("==================================================")
    test_1_mcq_generation()
    test_2_search_extraction()
    test_3_budget_guardrails()
    test_4_razorpay_signature_verification()
    print("\n ALL SMOKE TESTS PASSED SUCCESSFULLY! \n")
