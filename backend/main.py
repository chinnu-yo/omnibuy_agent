from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from schemas import (
    InitiateChatRequest, InitiateChatResponse,
    RecommendRequest, RecommendResponse,
    CreateOrderRequest, CreateOrderResponse,
    VerifyOrderRequest, VerifyOrderResponse,
    TraceLog
)
from agent import agent_engine, create_trace_log
from razorpay_service import create_order, verify_payment_signature

app = FastAPI(
    title="OmniBuyer Agent API",
    description="Backend AI Discovery & Autonomous Checkout Engine for Razorpay AI Buildathon",
    version="1.0.0"
)

# CORS Configuration strictly enabling Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "OmniBuyer Agent Backend"}

@app.post("/api/chat/initiate", response_model=InitiateChatResponse)
def initiate_chat(req: InitiateChatRequest):
    """
    Initiates conversational discovery by generating dynamic, 
    context-aware clarifying MCQs based on user intent and budget.
    """
    try:
        questions = agent_engine.generate_clarifying_mcqs(req.message, req.budget_cap)
        traces = [
            create_trace_log("INTENT_PARSED", f"Parsed discovery request for '{req.message}' with budget ceiling ₹{req.budget_cap:,.0f}"),
            create_trace_log("INTENT_PARSED", f"Generated {len(questions)} context-aware clarifying questions via Gemini reasoning", details={"questions": [q.model_dump() for q in questions]})
        ]
        return InitiateChatResponse(
            status="clarifying",
            questions=questions,
            traces=traces
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate discovery session: {str(e)}"
        )

@app.post("/api/chat/recommend", response_model=RecommendResponse)
def recommend_bundle(req: RecommendRequest):
    """
    Invokes Gemini Agent Engine to curate tiered real-market items, 
    applying deterministic Python price guardrails.
    """
    all_traces: List[TraceLog] = []
    try:
        all_traces.append(create_trace_log(
            stage="TOOL_INVOCATION",
            message=f"Gemini Agent Engine curating items for '{req.message}' with preferences: {req.user_selections}"
        ))

        bundle = agent_engine.build_bundle(
            user_intent=req.message,
            preferences=req.user_selections,
            budget_cap=req.budget_cap
        )

        all_traces.append(create_trace_log(
            stage="GUARDRAIL_ASSERTION",
            message=f"Deterministic Price Engine: Summed {len(bundle.items)} unique items -> Total: ₹{bundle.total_price:,.2f}",
            details={
                "item_prices": [item.price for item in bundle.items],
                "computed_sum": bundle.total_price,
                "budget_cap": bundle.budget_cap,
                "is_within_budget": bundle.is_within_budget
            }
        ))

        return RecommendResponse(
            status="ready",
            bundle=bundle,
            traces=all_traces
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assemble bundle recommendation: {str(e)}"
        )

@app.post("/api/order/create", response_model=CreateOrderResponse)
def create_razorpay_order_endpoint(req: CreateOrderRequest):
    """
    Creates Razorpay order (paise conversion). Rejects bundles violating budget ceiling.
    """
    try:
        order, key_id, traces = create_order(req.bundle)
        return CreateOrderResponse(
            order=order,
            key_id=key_id,
            traces=traces
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Razorpay order creation failed: {str(e)}"
        )

@app.post("/api/order/verify", response_model=VerifyOrderResponse)
def verify_payment_signature_endpoint(req: VerifyOrderRequest):
    """
    Cryptographically verifies Razorpay payment signature locally via HMAC SHA-256.
    """
    try:
        is_valid, msg, traces = verify_payment_signature(
            razorpay_order_id=req.razorpay_order_id,
            razorpay_payment_id=req.razorpay_payment_id,
            razorpay_signature=req.razorpay_signature
        )
        status_str = "SUCCESS" if is_valid else "FAILED"
        return VerifyOrderResponse(
            status=status_str,
            message=msg,
            traces=traces
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment signature verification failed: {str(e)}"
        )
