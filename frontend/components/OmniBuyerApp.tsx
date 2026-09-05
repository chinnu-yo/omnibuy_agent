'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Bot, 
  User, 
  Send, 
  RotateCcw, 
  CheckCircle2, 
  AlertCircle, 
  ExternalLink, 
  ShieldCheck, 
  ShoppingBag, 
  Cpu, 
  Search, 
  Calculator, 
  CreditCard,
  Check,
  Zap,
  Sparkles,
  DollarSign
} from 'lucide-react';

interface MCQOption {
  id: string;
  label: string;
  description: string;
}

interface MCQQuestion {
  question_id: string;
  question_text: string;
  options: MCQOption[];
}

interface BundleItem {
  title: string;
  price: number;
  source: string;
  url: string;
  category: string;
}

interface Bundle {
  bundle_name: string;
  items: BundleItem[];
  total_price: number;
  budget_cap: number;
  is_within_budget: boolean;
}

interface TraceLog {
  timestamp: string;
  stage: string;
  message: string;
  details?: any;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  mcqs?: MCQQuestion[];
  bundle?: Bundle;
  timestamp: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

export default function OmniBuyerApp() {
  const [sessionId, setSessionId] = useState<string>('');
  const [inputPrompt, setInputPrompt] = useState<string>('');
  const [budgetCap, setBudgetCap] = useState<number>(8000);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [userSelections, setUserSelections] = useState<Record<string, string>>({});
  const [activeMCQs, setActiveMCQs] = useState<MCQQuestion[]>([]);
  const [currentBundle, setCurrentBundle] = useState<Bundle | null>(null);
  const [ledgerTraces, setLedgerTraces] = useState<TraceLog[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingStage, setLoadingStage] = useState<string>('');
  const [paymentState, setPaymentState] = useState<'idle' | 'order_created' | 'verifying' | 'success' | 'failed'>('idle');
  const [verificationResult, setVerificationResult] = useState<{ status: string; message: string; payment_id?: string } | null>(null);

  const chatBottomRef = useRef<HTMLDivElement>(null);
  const ledgerBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSessionId('sess_' + Math.random().toString(36).substring(2, 9));
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, activeMCQs, currentBundle, isLoading]);

  useEffect(() => {
    ledgerBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [ledgerTraces]);

  const addTraceLogs = (newTraces?: TraceLog[]) => {
    if (newTraces && newTraces.length > 0) {
      setLedgerTraces(prev => [...prev, ...newTraces]);
    }
  };

  const handleResetSession = () => {
    setChatMessages([]);
    setUserSelections({});
    setActiveMCQs([]);
    setCurrentBundle(null);
    setLedgerTraces([]);
    setInputPrompt('');
    setPaymentState('idle');
    setVerificationResult(null);
  };

  // Phase 1: Initiate Discovery (Dynamic MCQs)
  const handleInitiateChat = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputPrompt.trim() || isLoading) return;

    const userText = inputPrompt.trim();
    setInputPrompt('');
    setIsLoading(true);
    setUserSelections({});
    setCurrentBundle(null);
    setPaymentState('idle');
    setVerificationResult(null);
    setLoadingStage('Parsing intent & generating clarifying questions...');

    const userMsg: ChatMessage = {
      id: 'msg_' + Date.now(),
      sender: 'user',
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages(prev => [...prev, userMsg]);

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat/initiate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: userText,
          budget_cap: budgetCap,
          user_selections: {}
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      
      addTraceLogs(data.traces);
      setActiveMCQs(data.questions || []);

      const qCount = data.questions?.length || 2;
      const agentMsg: ChatMessage = {
        id: 'msg_' + (Date.now() + 1),
        sender: 'agent',
        text: `I've analyzed your request for "${userText}". To curate the ideal setup within your ₹${budgetCap.toLocaleString('en-IN')} budget ceiling, please answer these ${qCount} quick preferences:`,
        mcqs: data.questions,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages(prev => [...prev, agentMsg]);

    } catch (err: any) {
      addTraceLogs([{
        timestamp: new Date().toLocaleTimeString(),
        stage: 'INTENT_PARSED',
        message: `Error connecting to backend API: ${err.message}`,
        details: { error: err.message }
      }]);
    } finally {
      setIsLoading(false);
      setLoadingStage('');
    }
  };

  // Handle Pill Chip Selection
  const handleSelectOption = (questionId: string, optionLabel: string) => {
    const updatedSelections = { ...userSelections, [questionId]: optionLabel };
    setUserSelections(updatedSelections);

    if (Object.keys(updatedSelections).length >= activeMCQs.length) {
      handleRecommendBundle(updatedSelections);
    }
  };

  // Phase 2: Live Sourcing & Deterministic Guardrail Recommendation
  const handleRecommendBundle = async (selections: Record<string, string>) => {
    setIsLoading(true);
    setLoadingStage('Sourcing live listings & evaluating price guardrails...');

    try {
      const lastUserMsg = [...chatMessages].reverse().find(m => m.sender === 'user')?.text || "Workstation Setup";
      
      const res = await fetch(`${API_BASE_URL}/api/chat/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: lastUserMsg,
          budget_cap: budgetCap,
          user_selections: selections
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      addTraceLogs(data.traces);
      setCurrentBundle(data.bundle);

      const agentMsg: ChatMessage = {
        id: 'msg_' + Date.now(),
        sender: 'agent',
        text: data.bundle.is_within_budget
          ? `✨ **Curated Bundle Ready!** Live market pricing verified strictly via backend mathematical engine.`
          : `⚠️ **Guardrail Alert:** Initial total exceeded budget limit. Self-healing engine autonomously adjusted items.`,
        bundle: data.bundle,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages(prev => [...prev, agentMsg]);
      setActiveMCQs([]);

    } catch (err: any) {
      addTraceLogs([{
        timestamp: new Date().toLocaleTimeString(),
        stage: 'GUARDRAIL_ASSERTION',
        message: `Recommendation Error: ${err.message}`,
        details: { error: err.message }
      }]);
    } finally {
      setIsLoading(false);
      setLoadingStage('');
    }
  };

  // Phase 3: Razorpay Order Creation & Checkout Modal Invocation
  const handleRazorpayCheckout = async () => {
    if (!currentBundle) return;

    setIsLoading(true);
    setLoadingStage('Creating Razorpay Sandbox Order...');

    try {
      const res = await fetch(`${API_BASE_URL}/api/order/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bundle: currentBundle })
      });

      if (!res.ok) {
        const errData = await res.json();
        console.error('[Razorpay Order Creation Error Payload]:', errData);
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      addTraceLogs(data.traces);
      setPaymentState('order_created');

      const { order, key_id } = data;
      const razorpayKey = key_id || 'rzp_test_TWjEsqvlRpx34H';

      if (!order || !order.id || !order.id.startsWith('order_')) {
        console.error('[Razorpay Order Format Error]: Backend returned non-standard order ID:', order);
        throw new Error(`Received invalid Razorpay order ID: ${order?.id}`);
      }

      if (typeof window !== 'undefined' && (window as any).Razorpay) {
        const options = {
          key: razorpayKey,
          amount: order.amount,
          currency: order.currency,
          name: "OmniBuyer Agent",
          description: currentBundle.bundle_name,
          order_id: order.id,
          handler: async function (response: any) {
            handleVerifyPayment(
              response.razorpay_order_id,
              response.razorpay_payment_id,
              response.razorpay_signature
            );
          },
          prefill: {
            name: "Buildathon Buyer",
            email: "buyer@omnibuyer.ai",
            contact: "9999999999"
          },
          theme: {
            color: "#10B981"
          }
        };

        const rzp = new (window as any).Razorpay(options);
        rzp.on('payment.failed', function (response: any) {
          addTraceLogs([{
            timestamp: new Date().toLocaleTimeString(),
            stage: 'RAZORPAY_STATE',
            message: `Razorpay Payment Cancelled: ${response.error?.description || 'Window closed'}`,
            details: response.error
          }]);
        });
        rzp.open();
      }

    } catch (err: any) {
      addTraceLogs([{
        timestamp: new Date().toLocaleTimeString(),
        stage: 'RAZORPAY_STATE',
        message: `Order Creation Failed: ${err.message}`,
        details: { error: err.message }
      }]);
      alert(`Order Creation Failed: ${err.message}`);
    } finally {
      setIsLoading(false);
      setLoadingStage('');
    }
  };

  // Phase 4: Cryptographic Payment Verification Handler
  const handleVerifyPayment = async (orderId: string, paymentId: string, signature: string) => {
    setPaymentState('verifying');
    setIsLoading(true);
    setLoadingStage('Verifying HMAC SHA-256 signature with backend SDK...');

    try {
      const res = await fetch(`${API_BASE_URL}/api/order/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          razorpay_order_id: orderId,
          razorpay_payment_id: paymentId,
          razorpay_signature: signature
        })
      });

      const data = await res.json();
      addTraceLogs(data.traces);

      if (data.status === 'SUCCESS') {
        setPaymentState('success');
        setVerificationResult({
          status: 'SUCCESS',
          message: data.message,
          payment_id: paymentId
        });

        // Post order placement & payment confirmation message directly into the CHAT WINDOW stream
        const confirmationMsg: ChatMessage = {
          id: 'msg_confirm_' + Date.now(),
          sender: 'agent',
          text: `🎉 **Order Placed & Payment Verified!**\n\nPayment signature cryptographically verified via Razorpay SDK (HMAC SHA-256).\n\n• **Payment ID:** \`${paymentId}\`\n• **Order ID:** \`${orderId}\`\n• **Status:** \`SETTLED & DISPATCHED\`\n\nYour order has been confirmed and submitted for fulfillment!`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setChatMessages(prev => [...prev, confirmationMsg]);
      } else {
        setPaymentState('failed');
        setVerificationResult({
          status: 'FAILED',
          message: data.message
        });

        const failureMsg: ChatMessage = {
          id: 'msg_failed_' + Date.now(),
          sender: 'agent',
          text: `❌ **Payment Verification Failed**\n\n${data.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setChatMessages(prev => [...prev, failureMsg]);
      }
    } catch (err: any) {
      setPaymentState('failed');
      addTraceLogs([{
        timestamp: new Date().toLocaleTimeString(),
        stage: 'CRYPTO_VERIFICATION',
        message: `Verification Error: ${err.message}`,
        details: { error: err.message }
      }]);
    } finally {
      setIsLoading(false);
      setLoadingStage('');
    }
  };

  const getStageBadgeColor = (stage: string) => {
    switch (stage) {
      case 'INTENT_PARSED': return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'TOOL_INVOCATION': return 'bg-violet-500/10 text-violet-400 border-violet-500/30';
      case 'GUARDRAIL_ASSERTION': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'RAZORPAY_STATE': return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'CRYPTO_VERIFICATION': return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      default: return 'bg-zinc-800 text-zinc-400 border-zinc-700';
    }
  };

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-zinc-100 font-sans overflow-hidden">
      
      {/* Top Header Bar */}
      <header className="h-14 border-b border-zinc-800 bg-zinc-900/60 backdrop-blur px-6 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Zap className="h-4 w-4" />
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-wide flex items-center gap-2">
              OmniBuyer Agent <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">Razorpay AI Buildathon</span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs">
          {/* Agent Status Badge */}
          <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-full">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-zinc-300 font-mono">Online - Gemini 2.5 Flash</span>
          </div>

          {/* Budget Ceiling Controls */}
          <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 px-3 py-1 rounded-lg">
            <DollarSign className="h-3.5 w-3.5 text-emerald-400" />
            <span className="text-zinc-400">Budget Cap:</span>
            <input
              type="number"
              value={budgetCap}
              onChange={(e) => setBudgetCap(Number(e.target.value))}
              suppressHydrationWarning
              className="w-20 bg-zinc-950 border border-zinc-700 rounded px-2 py-0.5 text-emerald-400 font-mono font-semibold text-xs focus:outline-none focus:border-emerald-500"
              step="500"
              min="1000"
            />
            <span className="text-zinc-400">INR</span>
          </div>

          {/* Reset Session */}
          <button
            onClick={handleResetSession}
            suppressHydrationWarning
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 transition text-xs"
            title="Reset Session"
          >
            <RotateCcw className="h-3.5 w-3.5 text-zinc-400" />
            <span>Reset</span>
          </button>
        </div>
      </header>

      {/* Main Split-Screen Layout */}
      <div className="flex-1 flex overflow-hidden">

        {/* Left Pane: Conversational Commerce Interface (60%) */}
        <div className="w-[60%] border-r border-zinc-800 flex flex-col bg-zinc-950">
          
          {/* Chat Messages Scroll Container */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">

            {chatMessages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4 text-zinc-400">
                <div className="h-12 w-12 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-emerald-400">
                  <Sparkles className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-zinc-200">Start Discovery Turn</h3>
                  <p className="text-xs text-zinc-400 mt-1">
                    Describe what you want to buy (e.g. FPS gaming gear, coding setup, audiophile desk setup). The agent will ask clarifying MCQs and dynamically harvest live market deals.
                  </p>
                </div>
                
                {/* Sample Prompt Chips */}
                <div className="flex flex-wrap gap-2 justify-center pt-2">
                  <button
                    onClick={() => {
                      setInputPrompt("I need a full competitive FPS gaming setup");
                    }}
                    suppressHydrationWarning
                    className="text-xs bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 px-3 py-1.5 rounded-full text-zinc-300 transition"
                  >
                    "Competitive FPS Gaming Setup"
                  </button>
                  <button
                    onClick={() => {
                      setInputPrompt("Curate a minimal developer desk setup");
                    }}
                    suppressHydrationWarning
                    className="text-xs bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 px-3 py-1.5 rounded-full text-zinc-300 transition"
                  >
                    "Minimal Developer Setup"
                  </button>
                </div>
              </div>
            )}

            {chatMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'agent' && (
                  <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0 mt-1">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div className={`max-w-[85%] space-y-3 ${msg.sender === 'user' ? 'bg-zinc-800/80 text-zinc-100 px-4 py-3 rounded-2xl rounded-tr-xs border border-zinc-700/50' : 'bg-zinc-900/90 border border-zinc-800 p-5 rounded-2xl rounded-tl-xs'}`}>
                  
                  <div className="text-sm leading-relaxed whitespace-pre-wrap">
                    {msg.text}
                  </div>

                  {/* Interactive MCQ Component */}
                  {msg.mcqs && msg.mcqs.length > 0 && (
                    <div className="space-y-4 pt-3 border-t border-zinc-800">
                      {msg.mcqs.map((q) => {
                        const selectedOptionLabel = userSelections[q.question_id];
                        return (
                          <div key={q.question_id} className="space-y-2 bg-zinc-950/60 p-3.5 rounded-xl border border-zinc-800/80">
                            <p className="text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
                              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                              {q.question_text}
                            </p>
                            
                            <div className="grid grid-cols-1 gap-2 pt-1">
                              {q.options.map((opt, idx) => {
                                const isSelected = selectedOptionLabel === opt.label;
                                return (
                                  <button
                                    key={opt.id}
                                    onClick={() => handleSelectOption(q.question_id, opt.label)}
                                    disabled={isLoading || !!selectedOptionLabel}
                                    suppressHydrationWarning
                                    className={`flex items-start justify-between p-3 rounded-lg border text-left transition ${
                                      isSelected
                                        ? 'bg-emerald-500/15 border-emerald-500 text-emerald-300'
                                        : selectedOptionLabel
                                        ? 'bg-zinc-900/50 border-zinc-800 text-zinc-500 cursor-not-allowed'
                                        : 'bg-zinc-900 border-zinc-800 hover:border-zinc-700 text-zinc-200 hover:bg-zinc-800/60'
                                    }`}
                                  >
                                    <div className="space-y-0.5 pr-2">
                                      <div className="text-xs font-medium flex items-center gap-2">
                                        <span className="font-mono text-[10px] text-zinc-400 bg-zinc-800 px-1.5 py-0.5 rounded">
                                          [{String.fromCharCode(65 + idx)}]
                                        </span>
                                        {opt.label}
                                      </div>
                                      <div className="text-[11px] text-zinc-400">{opt.description}</div>
                                    </div>

                                    {isSelected && (
                                      <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                                    )}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Curated Bundle Recommendation Card */}
                  {msg.bundle && (
                    <div className="space-y-4 pt-3 border-t border-zinc-800">
                      <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-800 space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                            <ShoppingBag className="h-4 w-4 text-emerald-400" />
                            {msg.bundle.bundle_name}
                          </h4>
                          
                          {/* Budget Status Badge */}
                          <span className={`text-[11px] font-mono px-2 py-0.5 rounded border ${
                            msg.bundle.is_within_budget
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          }`}>
                            {msg.bundle.is_within_budget ? 'PASSED: Within Budget Ceiling' : 'WARNING: Over Budget Ceiling'}
                          </span>
                        </div>

                        {/* Items Table */}
                        <div className="space-y-2 pt-1">
                          {msg.bundle.items.map((item, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-900/80 border border-zinc-800/80 text-xs"
                            >
                              <div className="space-y-0.5 pr-4 flex-1">
                                <div className="font-medium text-zinc-200 line-clamp-1">{item.title}</div>
                                <div className="flex items-center gap-2 text-[10px] text-zinc-400">
                                  <span className="px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-300 font-mono">{item.source}</span>
                                  <span>Category: {item.category}</span>
                                </div>
                              </div>
                              
                              <div className="text-right shrink-0">
                                <div className="font-mono font-semibold text-emerald-400">₹{item.price.toLocaleString('en-IN')}</div>
                                <a
                                  href={item.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-[10px] text-zinc-400 hover:text-emerald-400 flex items-center gap-1 justify-end transition"
                                >
                                  View Item <ExternalLink className="h-2.5 w-2.5" />
                                </a>
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Deterministic Price Summary */}
                        <div className="pt-2 border-t border-zinc-800/80 flex items-center justify-between text-xs">
                          <div className="space-y-0.5">
                            <div className="text-zinc-400">Deterministic Price Sum:</div>
                            <div className="text-[10px] text-zinc-500">Calculated strictly in Python</div>
                          </div>
                          <div className="text-right">
                            <div className="font-mono text-base font-bold text-emerald-400">
                              ₹{msg.bundle.total_price.toLocaleString('en-IN')}
                            </div>
                            <div className="text-[10px] text-zinc-400">Budget Limit: ₹{msg.bundle.budget_cap.toLocaleString('en-IN')}</div>
                          </div>
                        </div>

                        {/* Primary Razorpay Checkout CTA */}
                        {paymentState !== 'success' && (
                          <button
                            onClick={handleRazorpayCheckout}
                            disabled={isLoading || !msg.bundle.is_within_budget}
                            suppressHydrationWarning
                            className={`w-full mt-2 py-3 px-4 rounded-xl font-semibold text-xs flex items-center justify-center gap-2 transition shadow-lg ${
                              msg.bundle.is_within_budget
                                ? 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-zinc-950 shadow-emerald-500/10 cursor-pointer'
                                : 'bg-zinc-800 text-zinc-500 border border-zinc-700 cursor-not-allowed'
                            }`}
                          >
                            <CreditCard className="h-4 w-4" />
                            <span>Approve & Pay with Razorpay</span>
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="text-[10px] text-zinc-500 text-right pt-1">{msg.timestamp}</div>
                </div>

                {msg.sender === 'user' && (
                  <div className="h-8 w-8 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-300 shrink-0 mt-1">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex items-center gap-3 bg-zinc-900/60 border border-zinc-800/80 p-3.5 rounded-xl text-xs text-zinc-400 animate-pulse">
                <Bot className="h-4 w-4 text-emerald-400 animate-spin" />
                <span>{loadingStage || 'Processing agent reasoning engine...'}</span>
              </div>
            )}

            <div ref={chatBottomRef} />
          </div>

          {/* User Input Bar */}
          <form onSubmit={handleInitiateChat} className="p-4 border-t border-zinc-800 bg-zinc-900/40">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputPrompt}
                onChange={(e) => setInputPrompt(e.target.value)}
                placeholder="Type your purchase goal (e.g., 'Full competitive FPS gaming setup')..."
                disabled={isLoading}
                suppressHydrationWarning
                className="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500 transition"
              />
              <button
                type="submit"
                disabled={isLoading || !inputPrompt.trim()}
                suppressHydrationWarning
                className="bg-emerald-500 hover:bg-emerald-400 disabled:bg-zinc-800 disabled:text-zinc-600 text-zinc-950 font-semibold px-5 rounded-xl transition flex items-center justify-center text-xs"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </form>
        </div>

        {/* Right Pane: Monospace Real-Time Agent Thought & Guardrail Ledger (40%) */}
        <div className="w-[40%] flex flex-col bg-zinc-950 font-mono border-l border-zinc-800/80">
          
          {/* Ledger Header */}
          <div className="h-11 border-b border-zinc-800/80 bg-zinc-900/80 px-4 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2 text-xs text-zinc-300 font-medium">
              <Cpu className="h-4 w-4 text-violet-400" />
              <span>Thought & Guardrail Ledger</span>
            </div>
            <span className="text-[10px] text-zinc-500">{ledgerTraces.length} events logged</span>
          </div>

          {/* Log Stream Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {ledgerTraces.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-zinc-600 text-xs space-y-2">
                <Calculator className="h-6 w-6 text-zinc-700" />
                <p>Waiting for agent tool invocations and mathematical assertion logs...</p>
              </div>
            ) : (
              ledgerTraces.map((trace, idx) => (
                <div
                  key={idx}
                  className="bg-zinc-900/90 border border-zinc-800/90 rounded-lg p-3 space-y-1.5 text-[11px] leading-relaxed shadow-sm hover:border-zinc-700 transition"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${getStageBadgeColor(trace.stage)}`}>
                      [{trace.stage}]
                    </span>
                    <span className="text-[10px] text-zinc-500">{trace.timestamp}</span>
                  </div>

                  <p className="text-zinc-200 font-sans text-xs">{trace.message}</p>

                  {trace.details && (
                    <pre className="bg-zinc-950 p-2.5 rounded border border-zinc-800/80 text-[10px] text-zinc-400 overflow-x-auto">
                      {JSON.stringify(trace.details, null, 2)}
                    </pre>
                  )}
                </div>
              ))
            )}
            <div ref={ledgerBottomRef} />
          </div>

        </div>
      </div>
    </div>
  );
}
