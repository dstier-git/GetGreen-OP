import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export const ChatInput = ({ onSendMessage, disabled }: ChatInputProps) => {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about climate change, sustainability, or environmental solutions..."
        disabled={disabled}
        className="min-h-[60px] max-h-[200px] pr-12 resize-none focus-visible:ring-primary"
      />
      <Button
        type="submit"
        size="icon"
        disabled={disabled || !message.trim()}
        className="absolute right-2 bottom-2 h-8 w-8 bg-primary hover:bg-primary/90"
      >
        <Send className="h-4 w-4" />
      </Button>
    </form>
  );
};
