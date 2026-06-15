import { useState, useRef, useEffect } from "react";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import { Button } from "@/components/ui/button";
import getGreenLogo from "@/assets/getgreen-logo.png";
import { sendChatMessage, fetchWelcomeMessage, API_CONFIG } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const POC_USER_ID = 3421;
const MAX_HISTORY_TURNS = 16;
const DEFAULT_WELCOME =
  "Hi John — I’m GiGi, your personal sustainability assistant. I can see you’ve been doing great work on practical eco actions. You seem to like realistic changes, and you might be interested in trying one new low-effort step this week.";

const Index = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [provider, setProvider] = useState<"llama" | "chatgpt">("chatgpt");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    let cancelled = false;
    const loadWelcome = async () => {
      setIsTyping(true);
      try {
        const welcomeText = await fetchWelcomeMessage({
          userId: POC_USER_ID,
          provider: "chatgpt",
        });
        if (!cancelled) {
          setMessages([
            {
              id: "welcome",
              role: "assistant",
              content: welcomeText,
            },
          ]);
        }
      } catch {
        if (!cancelled) {
          setMessages([
            {
              id: "welcome-fallback",
              role: "assistant",
              content: DEFAULT_WELCOME,
            },
          ]);
        }
      } finally {
        if (!cancelled) {
          setIsTyping(false);
        }
      }
    };
    loadWelcome();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const history = [...messages, userMessage]
        .slice(-MAX_HISTORY_TURNS)
        .map(({ role, content }) => ({ role, content }));
      const responseText = await sendChatMessage(content, provider, {
        history,
        userId: POC_USER_ID,
      });
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: responseText,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      // #region agent log
      const err = error as Error;
      fetch("http://127.0.0.1:7244/ingest/d0b8079a-06bd-45a0-8a12-196e313fff53", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ location: "Index.tsx:handleSendMessage", message: "catch", data: { errorMessage: err?.message, errorName: err?.name }, timestamp: Date.now(), hypothesisId: "H1" }) }).catch(() => {});
      // #endregion
      console.error("Error calling API:", error);
      const errorContent =
        (error as Error)?.message ||
        `Sorry, I encountered an error. Please make sure the core backend is running at ${API_CONFIG.baseURL}.`;
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: errorContent,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-background to-muted">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
          <img 
            src={getGreenLogo} 
            alt="GetGreen Logo" 
            className="w-10 h-10 object-cover"
          />
          <div>
            <h1 className="text-xl font-semibold text-foreground">Climate Assistant</h1>
            <p className="text-xs text-muted-foreground">Sources actions and user data | Powered by {provider === "llama" ? "Llama" : "ChatGPT"}.</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Button
              type="button"
              size="sm"
              variant={provider === "llama" ? "default" : "outline"}
              onClick={() => setProvider("llama")}
            >
              Llama
            </Button>
            <Button
              type="button"
              size="sm"
              variant={provider === "chatgpt" ? "default" : "outline"}
              onClick={() => setProvider("chatgpt")}
            >
              ChatGPT
            </Button>
          </div>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              role={message.role}
              content={message.content}
            />
          ))}
          {isTyping && (
            <ChatMessage role="assistant" content="" isTyping />
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input */}
      <footer className="border-t border-border bg-card/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <ChatInput onSendMessage={handleSendMessage} disabled={isTyping} />
          <p className="text-xs text-muted-foreground text-center mt-2">
            Climate Assistant can make mistakes. Verify important information.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
