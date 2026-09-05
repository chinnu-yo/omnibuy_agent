import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agent import agent_engine

print("=== TEST 1: High Budget PC/Monitor Intent (Rs.3,00,000) ===")
intent1 = "I want a PC, monitor, and everything for heavy 4K gaming and 3D rendering"
budget1 = 300000.0

questions1 = agent_engine.generate_clarifying_mcqs(intent1, budget1)
print(f"Generated {len(questions1)} MCQs:")
for q in questions1:
    print(f" [{q.question_id}] {q.question_text}")
    for opt in q.options:
        print(f"   - {opt.label}: {opt.description}")

bundle1 = agent_engine.build_bundle(intent1, {"q1": "4K UHD Visual Fidelity", "q2": "Full ARGB Lighting"}, budget1)
print(f"\nBundle Name: {bundle1.bundle_name}")
print(f"Total Price: Rs.{bundle1.total_price:,.2f} (Within Budget: {bundle1.is_within_budget})")
print("Curated Items:")
for item in bundle1.items:
    print(f" * [{item.category}] {item.title} - Rs.{item.price:,.2f}")
    print(f"   URL: {item.url}")


print("\n=== TEST 2: Mid Budget Smartphone & Earbuds Intent (Rs.25,000) ===")
intent2 = "i need a 5G smart phone and active noise cancelling ear pods"
budget2 = 25000.0

questions2 = agent_engine.generate_clarifying_mcqs(intent2, budget2)
print(f"Generated {len(questions2)} MCQs:")
for q in questions2:
    print(f" [{q.question_id}] {q.question_text}")

bundle2 = agent_engine.build_bundle(intent2, {"q1": "120Hz AMOLED", "q2": "Active Noise Cancellation"}, budget2)
print(f"\nBundle Name: {bundle2.bundle_name}")
print(f"Total Price: Rs.{bundle2.total_price:,.2f} (Within Budget: {bundle2.is_within_budget})")
print("Curated Items:")
for item in bundle2.items:
    print(f" * [{item.category}] {item.title} - Rs.{item.price:,.2f}")
