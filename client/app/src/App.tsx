import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Send, User, Bot } from "lucide-react";

interface Message {
  id: number;
  text: string;
  sender: "user" | "bot";
  timestamp: Date;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hello! How can I help you today?",
      sender: "bot",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages]);

  const handleSendMessage = () => {
    if (inputValue.trim() === "") return;

    const newMessage: Message = {
      id: Date.now(),
      text: inputValue,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputValue("");

    // Simulate bot response with typing delay
    setTimeout(() => {
      const botResponse: Message = {
        id: Date.now() + 1,
        text: "Thanks for your message! This is a simple chat demo.",
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botResponse]);
    }, 1200);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50 p-2 sm:p-4 lg:p-6">
      <div className="w-full max-w-4xl mx-auto h-[calc(100vh-1rem)] sm:h-[calc(100vh-2rem)] lg:h-[calc(100vh-3rem)]">
        {/* Mobile-first approach with clean, minimal design */}
        <Card className="h-full flex flex-col border-0 shadow-sm bg-white">
          {/* Header - Rams principle: Honest and unobtrusive */}
          <CardHeader className="flex-shrink-0 border-b border-neutral-200 p-4 sm:p-6">
            <CardTitle className="text-lg sm:text-xl font-medium text-neutral-900 text-center tracking-tight">
              Chat
            </CardTitle>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
            {/* Messages Area - Maximum content, minimum chrome */}
            <ScrollArea
              ref={scrollAreaRef}
              className="flex-1 px-4 py-4 sm:px-6 sm:py-6"
            >
              <div className="space-y-4 sm:space-y-6">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex items-end gap-2 sm:gap-3 ${
                      message.sender === "user"
                        ? "justify-end"
                        : "justify-start"
                    }`}
                  >
                    {/* Bot Avatar - Only show on larger screens for cleaner mobile experience */}
                    {message.sender === "bot" && (
                      <Avatar className="w-7 h-7 sm:w-8 sm:h-8 hidden xs:flex flex-shrink-0">
                        <AvatarFallback className="bg-neutral-100 border border-neutral-200">
                          <Bot className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-neutral-600" />
                        </AvatarFallback>
                      </Avatar>
                    )}

                    <div className="flex flex-col max-w-[85%] sm:max-w-[75%] md:max-w-[65%]">
                      {/* Message bubble with Rams-inspired minimal styling */}
                      <div
                        className={`rounded-2xl px-3 py-2 sm:px-4 sm:py-3 ${
                          message.sender === "user"
                            ? "bg-neutral-900 text-white self-end"
                            : "bg-neutral-100 text-neutral-900 border border-neutral-200"
                        }`}
                      >
                        <p className="text-sm sm:text-base leading-relaxed break-words">
                          {message.text}
                        </p>
                      </div>

                      {/* Timestamp - Subtle and unobtrusive */}
                      <p
                        className={`text-xs text-neutral-500 mt-1 px-1 ${
                          message.sender === "user" ? "text-right" : "text-left"
                        }`}
                      >
                        {message.timestamp.toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>

                    {/* User Avatar - Only show on larger screens */}
                    {message.sender === "user" && (
                      <Avatar className="w-7 h-7 sm:w-8 sm:h-8 hidden xs:flex flex-shrink-0">
                        <AvatarFallback className="bg-neutral-900">
                          <User className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
                        </AvatarFallback>
                      </Avatar>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Input Area - Functional and accessible */}
            <div className="flex-shrink-0 border-t border-neutral-200 p-4 sm:p-6 bg-white">
              <div className="flex gap-2 sm:gap-3 items-end">
                <div className="flex-1">
                  <Input
                    placeholder="Type a message..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="min-h-[44px] sm:min-h-[48px] border-neutral-300 focus:border-neutral-400 focus:ring-1 focus:ring-neutral-400 resize-none rounded-xl bg-neutral-50 text-sm sm:text-base"
                    autoComplete="off"
                    autoCorrect="off"
                    spellCheck="false"
                  />
                </div>

                <Button
                  onClick={handleSendMessage}
                  disabled={inputValue.trim() === ""}
                  size="icon"
                  className="min-w-[44px] min-h-[44px] sm:min-w-[48px] sm:min-h-[48px] bg-neutral-900 hover:bg-neutral-800 disabled:bg-neutral-300 disabled:text-neutral-500 rounded-xl transition-all duration-200"
                >
                  <Send className="w-4 h-4 sm:w-5 sm:h-5" />
                  <span className="sr-only">Send message</span>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default App;
