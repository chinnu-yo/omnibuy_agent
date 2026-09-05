from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class TraceLog(BaseModel):
    timestamp: str
    stage: str  # e.g., INTENT_PARSED, TOOL_INVOCATION, GUARDRAIL_ASSERTION, RAZORPAY_STATE, CRYPTO_VERIFICATION
    message: str
    details: Optional[Dict[str, Any]] = None

class MCQOption(BaseModel):
    id: str
    label: str
    description: str

class MCQQuestion(BaseModel):
    question_id: str
    question_text: str
    options: List[MCQOption]

class InitiateChatRequest(BaseModel):
    session_id: str
    message: str
    budget_cap: float
    user_selections: Dict[str, str] = Field(default_factory=dict)

class InitiateChatResponse(BaseModel):
    status: str = "clarifying"
    questions: List[MCQQuestion]
    traces: List[TraceLog] = Field(default_factory=list)

class RecommendRequest(BaseModel):
    session_id: str
    message: str
    budget_cap: float
    user_selections: Dict[str, str]

class BundleItem(BaseModel):
    title: str
    price: float
    source: str
    url: str
    category: str

SourcedProduct = BundleItem

class Bundle(BaseModel):
    bundle_name: str
    items: List[BundleItem]
    total_price: float
    budget_cap: float
    is_within_budget: bool

RecommendedBundle = Bundle

class RecommendResponse(BaseModel):
    status: str = "ready"
    bundle: Bundle
    traces: List[TraceLog] = Field(default_factory=list)

class CreateOrderRequest(BaseModel):
    bundle: Bundle

class RazorpayOrder(BaseModel):
    id: str
    amount: int  # in paise
    currency: str = "INR"
    status: str = "created"

class CreateOrderResponse(BaseModel):
    order: RazorpayOrder
    key_id: str
    traces: List[TraceLog] = Field(default_factory=list)

class VerifyOrderRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class VerifyOrderResponse(BaseModel):
    status: str
    message: str
    traces: List[TraceLog] = Field(default_factory=list)
