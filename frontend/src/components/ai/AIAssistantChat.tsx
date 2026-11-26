import React, { useState, useRef, useEffect } from "react";
import { Bot, User, Send, Sparkles, ShieldAlert, TrendingUp, Info } from "lucide-react";
import { ChatMessage, AIDecisionResult } from "../../types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { apiService } from "../../services/api";

interface AIAssistantChatProps {
  initialTicker?: string;
  className?: string;
}

export const AIAssistantChat: React.FC<AIAssistantChatProps> = ({ initialTicker = "BBCA", className }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      sender: "assistant",
      content: `Halo! Saya **AI Scalping & Quantitative Trading Copilot**. Saya siap membantu menginterpretasikan model Deep Learning (LSTM & BiLSTM), indikator teknikal intraday, aturan fraksi BEI, dan manajemen risiko untuk saham **${initialTicker}** atau emiten lainnya.`,
      timestamp: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTicker, setSelectedTicker] = useState(initialTicker);
  const [decisionCard, setDecisionCard] = useState<AIDecisionResult | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedQuestions = [
    `Analisis peluang scalping ${selectedTicker}`,
    `Interpretasikan prediksi BiLSTM & LSTM ${selectedTicker}`,
    `Berapa estimasi fee transaksi (~0.48%) dan Stop Loss aman?`,
    `Apakah ada risiko false breakout pada volume saat ini?`,
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = async (queryText?: string) => {
    const text = queryText || inputValue;
    if (!text.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);

    try {
      // If asking for scalping analysis, also fetch structured decision card
      if (text.toLowerCase().includes("analisis") || text.toLowerCase().includes("scalping")) {
        const decision = await apiService.getAIDecision(selectedTicker);
        setDecisionCard(decision);
      }

      const botReply = await apiService.sendAIChat(text, selectedTicker);

      const assistantMsg: ChatMessage = {
        id: String(Date.now() + 1),
        sender: "assistant",
        content: botReply,
        timestamp: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`flex flex-col bg-[var(--card)] rounded-xl border border-[var(--border)] overflow-hidden shadow-xs ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-[var(--border)] bg-[var(--background)]/40">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-sm">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-sm text-[var(--text-primary)]">AI Scalping Copilot</h3>
              <Badge variant="primary">Active</Badge>
            </div>
            <p className="text-[11px] text-[var(--text-secondary)]">Grounded on Quant Engine & BEI Rules</p>
          </div>
        </div>

        {/* Ticker Selector Chip */}
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-[var(--text-secondary)]">Emiten:</span>
          <select
            value={selectedTicker}
            onChange={(e) => setSelectedTicker(e.target.value)}
            className="font-bold bg-[var(--card)] border border-[var(--border)] rounded-md px-2 py-1 text-[var(--text-primary)] focus:outline-none"
          >
            {["BBCA", "MEDC", "ADRO", "TLKM", "ASII", "BRIS"].map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Structured Decision Insight Card (if triggered) */}
      {decisionCard && (
        <div className="p-4 mx-4 mt-4 rounded-xl border border-blue-500/20 bg-blue-500/5 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-500" />
              <span className="font-bold text-[var(--text-primary)]">AI Decision: {decisionCard.stock_ticker}</span>
            </div>
            <Badge
              variant={
                decisionCard.decision === "BUY"
                  ? "buy"
                  : decisionCard.decision === "SELL"
                  ? "sell"
                  : decisionCard.decision === "HOLD"
                  ? "hold"
                  : "neutral"
              }
            >
              {decisionCard.decision}
            </Badge>
          </div>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            {decisionCard.detailed_explanation}
          </p>
          <div className="flex flex-wrap gap-3 pt-1 border-t border-[var(--border)] font-mono text-[11px]">
            <span>
              Entry: <strong>{decisionCard.entry_zone[0]} - {decisionCard.entry_zone[1]}</strong>
            </span>
            <span>
              SL: <strong className="text-rose-500">{decisionCard.stop_loss}</strong>
            </span>
            <span>
              TP: <strong className="text-emerald-500">{decisionCard.take_profit}</strong>
            </span>
            <span>
              RR Net: <strong className="text-blue-500">{decisionCard.net_risk_reward_ratio}x</strong>
            </span>
          </div>
        </div>
      )}

      {/* Message Stream */}
      <div className="flex-1 p-4 md:p-5 space-y-4 overflow-y-auto max-h-[420px] text-sm">
        {messages.map((msg) => {
          const isAssistant = msg.sender === "assistant";
          return (
            <div
              key={msg.id}
              className={`flex gap-3 ${isAssistant ? "items-start" : "items-start flex-row-reverse"}`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                  isAssistant
                    ? "bg-blue-600 text-white"
                    : "bg-[var(--border)] text-[var(--text-primary)]"
                }`}
              >
                {isAssistant ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
              </div>

              <div className={`max-w-[85%] space-y-1`}>
                <div
                  className={`p-3.5 rounded-2xl leading-relaxed whitespace-pre-wrap ${
                    isAssistant
                      ? "bg-[var(--background)] border border-[var(--border)] text-[var(--text-primary)]"
                      : "bg-blue-600 text-white shadow-xs"
                  }`}
                >
                  {msg.content}
                </div>
                <span className="text-[10px] text-[var(--text-secondary)] px-1 block">
                  {msg.timestamp}
                </span>
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex gap-3 items-center text-xs text-[var(--text-secondary)]">
            <div className="w-7 h-7 rounded-lg bg-blue-600/10 text-blue-500 flex items-center justify-center">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <span>AI Copilot sedang memverifikasi indikator kuantitatif...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompt Chips */}
      <div className="px-4 py-2 border-t border-[var(--border)] flex gap-2 overflow-x-auto no-scrollbar">
        {suggestedQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            disabled={isLoading}
            className="text-[11px] whitespace-nowrap px-3 py-1 rounded-full bg-[var(--background)] hover:bg-[var(--border)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors shrink-0"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-3 border-t border-[var(--border)] bg-[var(--background)]/30 flex items-center gap-2"
      >
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={`Tanyakan strategi scalping untuk ${selectedTicker}...`}
          className="flex-1 px-4 py-2 text-sm rounded-xl bg-[var(--card)] border border-[var(--border)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
        />
        <Button type="submit" disabled={!inputValue.trim() || isLoading} size="md">
          <Send className="w-4 h-4" />
        </Button>
      </form>

      {/* Regulatory Footer Disclaimer */}
      <div className="px-4 py-1.5 bg-[var(--background)] border-t border-[var(--border)] flex items-center justify-between text-[10px] text-[var(--text-secondary)]">
        <span className="flex items-center gap-1">
          <ShieldAlert className="w-3 h-3 text-amber-500 shrink-0" />
          AI asisten analisis kuantitatif; bukan jaminan keuntungan bursa.
        </span>
        <span className="hidden sm:inline">1 Lot = 100 lembar | Fee ~0.48%</span>
      </div>
    </div>
  );
};
