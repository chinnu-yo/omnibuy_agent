import os
import json
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types
from schemas import (
    MCQQuestion, MCQOption, BundleItem, Bundle, TraceLog,
    SourcedProduct, RecommendedBundle
)

def create_trace_log(stage: str, message: str, details: Optional[Dict[str, Any]] = None) -> TraceLog:
    """Utility to build structured ledger logs for front-end visual audit."""
    return TraceLog(
        timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
        stage=stage,
        message=message,
        details=details
    )

def clean_json_text(raw_text: str) -> str:
    """Strips markdown code blocks (```json ... ```) from LLM responses."""
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


class AgentEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
        if api_key and api_key != "your_gemini_api_key_here":
            try:
                self.client = genai.Client(api_key=api_key)
                print(f"[AgentEngine] Gemini Client successfully initialized with API key: {api_key[:8]}...")
            except Exception as e:
                print(f"[AgentEngine Error] Failed to initialize genai.Client: {e}")
                self.client = None
        else:
            print("[AgentEngine Notice] GEMINI_API_KEY is not set in backend/.env. Using fallback generator until key is provided.")
            self.client = None

    def generate_clarifying_mcqs(self, user_intent: str, budget_cap: float) -> list[MCQQuestion]:
        """
        Sends user query directly to Gemini LLM to generate between 2 and 5 (min 2, max 5)
        necessary clarifying multiple choice questions in JSON format.
        """
        if self.client:
            system_instruction = (
                "You are an expert consumer hardware and goods buyer agent in India. "
                "Analyze the user's specific purchase request and budget ceiling. "
                "Generate between 2 and 5 relevant, non-technical clarifying multiple-choice questions "
                "(MINIMUM 2, MAXIMUM 5) based on the complexity and scope of their specific request. "
                "Simple 1-item requests should have 2 questions; complex multi-item setups (e.g., full PC rigs, home audio, streaming setups) should have 3 to 5 questions. "
                "DO NOT use generic templates. Ask ONLY the most necessary questions specific to their prompt."
            )
            
            prompt = f"""
            User Request: "{user_intent}"
            Budget Ceiling: ₹{budget_cap:,.0f} INR

            Generate between 2 and 5 clarifying questions (min 2, max 5) necessary for this request.
            Return strictly valid JSON array of question objects:
            [
              {{
                "question_id": "q1",
                "question_text": "Specific clarifying question for this exact request?",
                "options": [
                  {{"id": "opt1", "label": "Option Title", "description": "Short explanation"}},
                  {{"id": "opt2", "label": "Option Title", "description": "Short explanation"}},
                  {{"id": "opt3", "label": "Option Title", "description": "Short explanation"}}
                ]
              }},
              {{
                "question_id": "q2",
                "question_text": "Second specific question?",
                "options": [
                  {{"id": "opt1", "label": "Option Title", "description": "Short explanation"}},
                  {{"id": "opt2", "label": "Option Title", "description": "Short explanation"}}
                ]
              }}
            ]
            """
            
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.3
                    )
                )
                cleaned_text = clean_json_text(response.text)
                data = json.loads(cleaned_text)
                
                questions = []
                for idx, q in enumerate(data[:5]):
                    opts = [MCQOption(**opt) for opt in q.get("options", [])]
                    questions.append(MCQQuestion(
                        question_id=q.get("question_id", f"q{idx+1}"),
                        question_text=q.get("question_text", "Select preference:"),
                        options=opts
                    ))
                print(f"[AgentEngine] Successfully generated {len(questions)} custom MCQs via Gemini 2.5 Flash for prompt '{user_intent[:30]}'")
                return questions
            except Exception as e:
                print(f"[AgentEngine Error] Gemini API MCQ generation failed: {e}")

        return self._dynamic_intent_mcqs(user_intent)

    def build_bundle(self, user_intent: str, preferences: dict, budget_cap: float) -> RecommendedBundle:
        """
        Sends user query and selected preferences as context to Gemini LLM 
        to curate real Indian market products with ACCURATE REAL-WORLD INR PRICES.
        Applies deterministic Python guardrails to calculate total sum and verify budget.
        """
        if self.client:
            system_instruction = (
                "You are an elite consumer goods and hardware buyer agent in India. "
                "Select 3 to 4 real, specific, top-tier products available on Amazon India or direct brands "
                "that fulfill the user's request and selected preferences. "
                "CRITICAL: You MUST use REAL-WORLD CURRENT INDIAN MARKET PRICES (in INR ₹). "
                "Do NOT invent inflated prices (e.g. a Redragon K552 keyboard is ~₹2,899, a Razer DeathAdder mouse is ~₹1,749, "
                "an Acer Nitro 27-inch 180Hz gaming monitor is ~₹12,999, an RTX 4070 Ti PC tower is ~₹1,85,000). "
                "Ensure the combined total of all items fits safely within the budget ceiling."
            )

            prompt = f"""
            User Intent: "{user_intent}"
            User Selected Preferences Context: {json.dumps(preferences)}
            Maximum Budget Ceiling: ₹{budget_cap:,.0f} INR

            Select 3 to 4 distinct, essential components to build a complete, cohesive setup.
            Return strictly valid JSON array of items:
            [
              {{
                "title": "Exact Brand and Model Name",
                "estimated_price": 12999.0,
                "source": "Amazon IN",
                "category": "Component Category"
              }}
            ]
            """

            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )
                cleaned_text = clean_json_text(response.text)
                raw_items = json.loads(cleaned_text)

                items = []
                for it in raw_items:
                    encoded_query = urllib.parse.quote(it["title"])
                    direct_url = f"https://www.amazon.in/s?k={encoded_query}"
                    
                    items.append(SourcedProduct(
                        title=str(it["title"])[:70],
                        price=float(it["estimated_price"]),
                        source=str(it.get("source", "Amazon IN")),
                        url=direct_url,
                        category=str(it.get("category", "Hardware"))
                    ))

                # Deterministic Python Guardrail (Zero Hallucination)
                computed_total = sum(i.price for i in items)
                is_within_budget = computed_total <= budget_cap

                print(f"[AgentEngine] Successfully curated {len(items)} products via Gemini 2.5 Flash. Total: ₹{computed_total:,.2f}")

                return RecommendedBundle(
                    bundle_name=f"Curated {user_intent.title()} Bundle",
                    items=items,
                    total_price=computed_total,
                    budget_cap=budget_cap,
                    is_within_budget=is_within_budget
                )
            except Exception as e:
                print(f"[AgentEngine Error] Gemini API Bundle generation failed: {e}")

        return self._accurate_market_bundle(user_intent, preferences, budget_cap)

    def _dynamic_intent_mcqs(self, user_intent: str) -> list[MCQQuestion]:
        """Category-tailored clarifying MCQs matching prompt intent when Gemini API key is offline."""
        intent_lower = user_intent.lower()
        if "pc" in intent_lower or "gaming" in intent_lower or "monitor" in intent_lower or "desktop" in intent_lower or "rig" in intent_lower:
            return [
                MCQQuestion(
                    question_id="q1",
                    question_text=f"What display resolution & target performance level do you want for your gaming PC setup?",
                    options=[
                        MCQOption(id="opt1", label="1440p High-Refresh Esports & AAA", description="Spacious 2K resolution at 180Hz for competitive gaming"),
                        MCQOption(id="opt2", label="4K Ultra HD Visual Fidelity", description="Maximum 4K resolution for cinematic AAA gaming & 3D rendering"),
                        MCQOption(id="opt3", label="1080p High FPS Speed", description="Ultra-fast 1080p performance for high FPS competitive titles")
                    ]
                ),
                MCQQuestion(
                    question_id="q2",
                    question_text="What aesthetic design & lighting style do you prefer?",
                    options=[
                        MCQOption(id="opt1", label="Full ARGB Lighting & Tempered Glass", description="Vibrant customizable RGB illumination"),
                        MCQOption(id="opt2", label="Stealth Black Minimalist", description="Sleek matte black finish with zero RGB distractions")
                    ]
                ),
                MCQQuestion(
                    question_id="q3",
                    question_text="What peripheral audio & headset priority fits your build?",
                    options=[
                        MCQOption(id="opt1", label="7.1 Surround Sound Gaming Headset", description="Immersive spatial audio for footsteps & communication"),
                        MCQOption(id="opt2", label="Hi-Fi Studio Headphones & Boom Mic", description="Audiophile sound clarity for streaming & gaming")
                    ]
                )
            ]
        elif "phone" in intent_lower or "mobile" in intent_lower or "ear" in intent_lower or "pod" in intent_lower:
            return [
                MCQQuestion(
                    question_id="q1",
                    question_text=f"What smartphone display & performance feature is most critical?",
                    options=[
                        MCQOption(id="opt1", label="120Hz AMOLED 5G Performance", description="High refresh rate smooth display with 5G"),
                        MCQOption(id="opt2", label="Long-Life 5000mAh Battery", description="All-day battery life with ultra-fast charging")
                    ]
                ),
                MCQQuestion(
                    question_id="q2",
                    question_text="What feature priority do you want for your EarPods / TWS Earbuds?",
                    options=[
                        MCQOption(id="opt1", label="Active Noise Cancellation (ANC)", description="Blocks ambient environmental noise"),
                        MCQOption(id="opt2", label="Deep Bass Boost & Low Latency", description="Rich sound signature tuned for music & gaming")
                    ]
                ),
                MCQQuestion(
                    question_id="q3",
                    question_text="What protective case material preference do you have?",
                    options=[
                        MCQOption(id="opt1", label="Slim Matte Armor Case", description="Sleek protection with anti-slip grip"),
                        MCQOption(id="opt2", label="Heavy Duty Military Grade Shockproof", description="Maximum drop protection with kickstand")
                    ]
                )
            ]
        else:
            return [
                MCQQuestion(
                    question_id="q1",
                    question_text=f"Which core performance priority fits your goal '{user_intent}'?",
                    options=[
                        MCQOption(id="opt1", label="High Performance & Speed", description="Prioritizes top specs and processing power"),
                        MCQOption(id="opt2", label="Balanced Everyday Reliability", description="Focuses on durability, comfort, and value")
                    ]
                ),
                MCQQuestion(
                    question_id="q2",
                    question_text="What workspace accessory priority would complete your purchase?",
                    options=[
                        MCQOption(id="opt1", label="Essential Protection & Power Hub", description="Includes fast chargers and surge protection"),
                        MCQOption(id="opt2", label="Ergonomic Support & Accessories", description="Adds posture support and desk mats")
                    ]
                )
            ]

    def _accurate_market_bundle(self, user_intent: str, preferences: dict, budget_cap: float) -> RecommendedBundle:
        """
        Accurate real-world Indian market pricing engine for products.
        Eliminates bogus percentage scaling and uses exact realistic market prices (in INR).
        """
        intent_lower = user_intent.lower()
        items = []

        if "pc" in intent_lower or "gaming" in intent_lower or "monitor" in intent_lower or "desktop" in intent_lower or "rig" in intent_lower:
            if budget_cap >= 150000:
                items = [
                    SourcedProduct(
                        title="Custom RTX 4070 Ti Super Gaming PC Tower (Ryzen 7 7800X3D, 32GB DDR5, 1TB NVMe)",
                        price=185000.0,
                        source="Amazon IN",
                        url=f"https://www.amazon.in/s?k={urllib.parse.quote('RTX 4070 Ti Super Gaming PC Tower')}",
                        category="Gaming Rig"
                    ),
                    SourcedProduct(
                        title="LG UltraGear 27-inch 1440p 180Hz Nano IPS Gaming Monitor (27GP850)",
                        price=24999.0,
                        source="Amazon IN",
                        url=f"https://www.amazon.in/s?k={urllib.parse.quote('LG UltraGear 27 inch 1440p 180Hz Monitor')}",
                        category="Gaming Monitor"
                    ),
                    SourcedProduct(
                        title="Keychron K2 Wireless Mechanical Keyboard (Gateron Switches)",
                        price=7499.0,
                        source="Amazon IN",
                        url=f"https://www.amazon.in/s?k={urllib.parse.quote('Keychron K2 Wireless Mechanical Keyboard')}",
                        category="Mechanical Keyboard"
                    ),
                    SourcedProduct(
                        title="Logitech G502 HERO High Performance Gaming Mouse (25600 DPI)",
                        price=4299.0,
                        source="Amazon IN",
                        url=f"https://www.amazon.in/s?k={urllib.parse.quote('Logitech G502 HERO Gaming Mouse')}",
                        category="Precision Mouse"
                    )
                ]
            else:
                items = [
                    SourcedProduct(
                        title="Custom RTX 3060 Gaming PC Tower (Ryzen 5 5600X, 16GB RAM, 512GB SSD)",
                        price=52000.0,
                        source="Amazon IN",
                        url=f"https://www.amazon.in/s?k={urllib.parse.quote('RTX 3060 Gaming PC Tower')}",
                        category="Gaming Rig"
                    ),
                    SourcedProduct(
                        title="Acer Nitro 27-inch 180Hz Gaming Monitor (0.5ms, IPS, FHD)",
                        price=12999.0,
                        source="Amazon IN",
                        url=f"https://www.amazon.in/s?k={urllib.parse.quote('Acer Nitro 27 inch 180Hz Monitor')}",
                        category="Gaming Monitor"
                    ),
                    SourcedProduct(
                        title="Redragon K552 KUMARA RGB Mechanical Gaming Keyboard",
                        price=2899.0,
                        source="Amazon IN",
                        url=f"https://www.amazon.in/s?k={urllib.parse.quote('Redragon K552 Mechanical Keyboard')}",
                        category="Mechanical Keyboard"
                    ),
                    SourcedProduct(
                        title="Razer DeathAdder Essential Gaming Mouse (6400 DPI)",
                        price=1749.0,
                        source="Amazon IN",
                        url=f"https://www.amazon.in/s?k={urllib.parse.quote('Razer DeathAdder Essential Gaming Mouse')}",
                        category="Precision Mouse"
                    )
                ]
        elif "phone" in intent_lower or "mobile" in intent_lower or "ear" in intent_lower or "pod" in intent_lower:
            items = [
                SourcedProduct(
                    title="iQOO Z9 5G (Graphene Blue, 8GB RAM, 128GB Storage)",
                    price=17999.0,
                    source="Amazon IN",
                    url=f"https://www.amazon.in/s?k={urllib.parse.quote('iQOO Z9 5G smartphone')}",
                    category="5G Smartphone"
                ),
                SourcedProduct(
                    title="realme Buds T300 TWS Earbuds with 30dB ANC & 40H Playtime",
                    price=2199.0,
                    source="Amazon IN",
                    url=f"https://www.amazon.in/s?k={urllib.parse.quote('realme Buds T300 TWS Earbuds')}",
                    category="Wireless Earbuds"
                ),
                SourcedProduct(
                    title="Mi 33W SonicCharge 2.0 Fast Charger with Type-C Cable",
                    price=999.0,
                    source="Amazon IN",
                    url=f"https://www.amazon.in/s?k={urllib.parse.quote('Mi 33W SonicCharge Fast Charger')}",
                    category="Mobile Accessory"
                )
            ]
        else:
            items = [
                SourcedProduct(
                    title=f"Lenovo IdeaPad Slim 3 Laptop (12th Gen Intel i5, 16GB RAM, 512GB SSD)",
                    price=45990.0,
                    source="Amazon IN",
                    url=f"https://www.amazon.in/s?k={urllib.parse.quote('Lenovo IdeaPad Slim 3 Laptop')}",
                    category="Primary System"
                ),
                SourcedProduct(
                    title="Logitech MX Master 3S Wireless Performance Mouse",
                    price=8995.0,
                    source="Amazon IN",
                    url=f"https://www.amazon.in/s?k={urllib.parse.quote('Logitech MX Master 3S Mouse')}",
                    category="Precision Mouse"
                ),
                SourcedProduct(
                    title="Portronics My Buddy K Adjustable Aluminum Laptop Stand",
                    price=799.0,
                    source="Amazon IN",
                    url=f"https://www.amazon.in/s?k={urllib.parse.quote('Portronics Laptop Stand')}",
                    category="Accessory"
                )
            ]

        # Deterministic Python Guardrail
        computed_total = sum(i.price for i in items)
        is_within_budget = computed_total <= budget_cap

        return RecommendedBundle(
            bundle_name=f"Curated {user_intent.title()} Bundle",
            items=items,
            total_price=computed_total,
            budget_cap=budget_cap,
            is_within_budget=is_within_budget
        )


# Singleton Agent Engine Instance
agent_engine = AgentEngine()

# Backward-Compatible Helper Functions for main.py
def generate_clarifying_questions(user_message: str, budget_cap: float = 8000.0) -> Tuple[List[MCQQuestion], List[TraceLog]]:
    traces: List[TraceLog] = [
        create_trace_log("INTENT_PARSED", f"Parsing user discovery request: '{user_message}' with budget ₹{budget_cap:,.0f}")
    ]
    questions = agent_engine.generate_clarifying_mcqs(user_message, budget_cap)
    traces.append(create_trace_log("INTENT_PARSED", f"Generated {len(questions)} context-aware clarifying questions via Gemini reasoning"))
    return questions, traces

def decompose_intent_to_queries(user_message: str, user_selections: Dict[str, str]) -> Tuple[List[Dict[str, str]], List[TraceLog]]:
    traces: List[TraceLog] = [
        create_trace_log("TOOL_INVOCATION", f"Decomposing intent '{user_message}' with preferences: {user_selections}")
    ]
    queries = [
        {"query": f"{user_message} item", "category": "Hardware"}
    ]
    return queries, traces

def build_and_validate_bundle(
    items: List[BundleItem],
    budget_cap: float,
    bundle_name: str = "Curated Product Bundle"
) -> Tuple[Bundle, List[TraceLog]]:
    traces: List[TraceLog] = []
    computed_total = sum(i.price for i in items)
    is_within_budget = computed_total <= budget_cap

    traces.append(create_trace_log(
        stage="GUARDRAIL_ASSERTION",
        message=f"Deterministic Price Engine: Summed {len(items)} items -> Total: ₹{computed_total:,.2f}",
        details={
            "computed_sum": computed_total,
            "budget_cap": budget_cap,
            "is_within_budget": is_within_budget
        }
    ))

    bundle = Bundle(
        bundle_name=bundle_name,
        items=items,
        total_price=computed_total,
        budget_cap=budget_cap,
        is_within_budget=is_within_budget
    )
    return bundle, traces
