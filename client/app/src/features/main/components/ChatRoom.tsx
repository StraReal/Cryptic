import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Paperclip, SendHorizonal, Smile } from "lucide-react";

interface Message {
  id: string;
  text: string;
  sender: string;
  timestamp: string;
}

interface ChatRoomProps {
  roomCode: string;
  username: string;
  onLeave: () => void;
  sendMessage: (payload: object) => void;
  messages: Message[];
}

export const ChatRoom: React.FC<ChatRoomProps> = ({
  roomCode,
  username,
  onLeave,
  sendMessage,
  messages,
}) => {
  const [newMessage, setNewMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (newMessage.trim()) {
      sendMessage({
        type: "message",
        room: roomCode,
        from: username,
        text: newMessage,
      });
      setNewMessage("");
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <header className="flex items-center justify-between p-4 border-b bg-white">
        <div>
          <h2 className="text-xl font-bold">Room: {roomCode}</h2>
          <p className="text-sm text-gray-500">Logged in as: {username}</p>
        </div>
        <Button variant="outline" onClick={onLeave}>
          Leave Room
        </Button>
      </header>

      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.sender === username ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-xs md:max-w-md p-3 rounded-lg ${
                  msg.sender === username
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <p className="font-bold text-sm">{msg.sender}</p>
                <p>{msg.text}</p>
                <p className="text-xs text-right opacity-75 mt-1">{msg.timestamp}</p>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </main>

      <footer className="p-4 bg-white border-t">
        <form onSubmit={handleSendMessage} className="flex items-center space-x-2">
          <Button variant="ghost" size="icon">
            <Paperclip className="w-5 h-5" />
          </Button>
          <Button variant="ghost" size="icon">
            <Smile className="w-5 h-5" />
          </Button>
          <Input
            type="text"
            placeholder="Type a message..."
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            className="flex-1"
          />
          <Button type="submit" size="icon">
            <SendHorizonal className="w-5 h-5" />
          </Button>
        </form>
      </footer>
    </div>
  );
};
