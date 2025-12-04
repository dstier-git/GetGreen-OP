import { useState, useRef, useEffect } from "react";
import { ChatMessage } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";
import climateLogo from "@/assets/climate-logo.png";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const Index = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! I'm your Climate Assistant. I'm here to help you understand climate change, explore sustainable solutions, and answer your environmental questions. What would you like to know?",
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: content }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error calling API:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error while processing your request. Please make sure the backend server is running on http://localhost:8000",
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
            src={climateLogo} 
            alt="Climate Assistant Logo" 
            className="w-10 h-10 object-cover"
          />
          <div>
            <h1 className="text-xl font-semibold text-foreground">Climate Assistant</h1>
            <p className="text-xs text-muted-foreground">Sources actions and user data | Powered by Llama.</p>
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
