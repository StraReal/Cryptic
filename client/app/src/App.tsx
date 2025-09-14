// import { useState, useRef, useEffect } from "react";
// import { Button } from "@/components/ui/button";
// import { Input } from "@/components/ui/input";
// import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// import { ScrollArea } from "@/components/ui/scroll-area";
// import { Avatar, AvatarFallback } from "@/components/ui/avatar";
// import { Send, User, Bot } from "lucide-react";

// interface Message {
//   id: number;
//   text: string;
//   sender: "user" | "bot";
//   timestamp: Date;
// }

// function App() {
//   const [messages, setMessages] = useState<Message[]>([
//     {
//       id: 1,
//       text: "Hello! How can I help you today?",
//       sender: "bot",
//       timestamp: new Date(),
//     },
//   ]);
//   const [inputValue, setInputValue] = useState("");
//   const scrollAreaRef = useRef<HTMLDivElement>(null);

//   // Auto-scroll to bottom when new messages arrive
//   useEffect(() => {
//     if (scrollAreaRef.current) {
//       const scrollContainer = scrollAreaRef.current.querySelector(
//         "[data-radix-scroll-area-viewport]"
//       );
//       if (scrollContainer) {
//         scrollContainer.scrollTop = scrollContainer.scrollHeight;
//       }
//     }
//   }, [messages]);

//   const handleSendMessage = () => {
//     if (inputValue.trim() === "") return;

//     const newMessage: Message = {
//       id: Date.now(),
//       text: inputValue,
//       sender: "user",
//       timestamp: new Date(),
//     };

//     setMessages((prev) => [...prev, newMessage]);
//     setInputValue("");

//     // Simulate bot response with typing delay
//     setTimeout(() => {
//       const botResponse: Message = {
//         id: Date.now() + 1,
//         text: "Thanks for your message! This is a simple chat demo.",
//         sender: "bot",
//         timestamp: new Date(),
//       };
//       setMessages((prev) => [...prev, botResponse]);
//     }, 1200);
//   };

//   const handleKeyDown = (e: React.KeyboardEvent) => {
//     if (e.key === "Enter" && !e.shiftKey) {
//       e.preventDefault();
//       handleSendMessage();
//     }
//   };

//   return (
//     <div className="min-h-screen bg-neutral-50 p-2 sm:p-4 lg:p-6">
//       <div className="w-full max-w-4xl mx-auto h-[calc(100vh-1rem)] sm:h-[calc(100vh-2rem)] lg:h-[calc(100vh-3rem)]">
//         {/* Mobile-first approach with clean, minimal design */}
//         <Card className="h-full flex flex-col border-0 shadow-sm bg-white">
//           {/* Header - Rams principle: Honest and unobtrusive */}
//           <CardHeader className="flex-shrink-0 border-b border-neutral-200 p-4 sm:p-6">
//             <CardTitle className="text-lg sm:text-xl font-medium text-neutral-900 text-center tracking-tight">
//               Chat
//             </CardTitle>
//           </CardHeader>

//           <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
//             {/* Messages Area - Maximum content, minimum chrome */}
//             <ScrollArea
//               ref={scrollAreaRef}
//               className="flex-1 px-4 py-4 sm:px-6 sm:py-6"
//             >
//               <div className="space-y-4 sm:space-y-6">
//                 {messages.map((message) => (
//                   <div
//                     key={message.id}
//                     className={`flex items-end gap-2 sm:gap-3 ${
//                       message.sender === "user"
//                         ? "justify-end"
//                         : "justify-start"
//                     }`}
//                   >
//                     {/* Bot Avatar - Only show on larger screens for cleaner mobile experience */}
//                     {message.sender === "bot" && (
//                       <Avatar className="w-7 h-7 sm:w-8 sm:h-8 hidden xs:flex flex-shrink-0">
//                         <AvatarFallback className="bg-neutral-100 border border-neutral-200">
//                           <Bot className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-neutral-600" />
//                         </AvatarFallback>
//                       </Avatar>
//                     )}

//                     <div className="flex flex-col max-w-[85%] sm:max-w-[75%] md:max-w-[65%]">
//                       {/* Message bubble with Rams-inspired minimal styling */}
//                       <div
//                         className={`rounded-2xl px-3 py-2 sm:px-4 sm:py-3 ${
//                           message.sender === "user"
//                             ? "bg-neutral-900 text-white self-end"
//                             : "bg-neutral-100 text-neutral-900 border border-neutral-200"
//                         }`}
//                       >
//                         <p className="text-sm sm:text-base leading-relaxed break-words">
//                           {message.text}
//                         </p>
//                       </div>

//                       {/* Timestamp - Subtle and unobtrusive */}
//                       <p
//                         className={`text-xs text-neutral-500 mt-1 px-1 ${
//                           message.sender === "user" ? "text-right" : "text-left"
//                         }`}
//                       >
//                         {message.timestamp.toLocaleTimeString([], {
//                           hour: "2-digit",
//                           minute: "2-digit",
//                         })}
//                       </p>
//                     </div>

//                     {/* User Avatar - Only show on larger screens */}
//                     {message.sender === "user" && (
//                       <Avatar className="w-7 h-7 sm:w-8 sm:h-8 hidden xs:flex flex-shrink-0">
//                         <AvatarFallback className="bg-neutral-900">
//                           <User className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
//                         </AvatarFallback>
//                       </Avatar>
//                     )}
//                   </div>
//                 ))}
//               </div>
//             </ScrollArea>

//             {/* Input Area - Functional and accessible */}
//             <div className="flex-shrink-0 border-t border-neutral-200 p-4 sm:p-6 bg-white">
//               <div className="flex gap-2 sm:gap-3 items-end">
//                 <div className="flex-1">
//                   <Input
//                     placeholder="Type a message..."
//                     value={inputValue}
//                     onChange={(e) => setInputValue(e.target.value)}
//                     onKeyDown={handleKeyDown}
//                     className="min-h-[44px] sm:min-h-[48px] border-neutral-300 focus:border-neutral-400 focus:ring-1 focus:ring-neutral-400 resize-none rounded-xl bg-neutral-50 text-sm sm:text-base"
//                     autoComplete="off"
//                     autoCorrect="off"
//                     spellCheck="false"
//                   />
//                 </div>

//                 <Button
//                   onClick={handleSendMessage}
//                   disabled={inputValue.trim() === ""}
//                   size="icon"
//                   className="min-w-[44px] min-h-[44px] sm:min-w-[48px] sm:min-h-[48px] bg-neutral-900 hover:bg-neutral-800 disabled:bg-neutral-300 disabled:text-neutral-500 rounded-xl transition-all duration-200"
//                 >
//                   <Send className="w-4 h-4 sm:w-5 sm:h-5" />
//                   <span className="sr-only">Send message</span>
//                 </Button>
//               </div>
//             </div>
//           </CardContent>
//         </Card>
//       </div>
//     </div>
//   );
// }

// export default App;

import { useState } from "react";

interface RoomResult {
  error?: string;
  status?: string;
  room_code?: string;
  my_port?: string;
  my_ip?: string;
  message?: string;
  rawOutput?: string;
  stderr?: string;
}

function App() {
  const [serverUrl, setServerUrl] = useState(
    "https://signalingserverdomain.download"
  );
  const [roomCode, setRoomCode] = useState("");
  const [username, setUsername] = useState("");
  const [result, setResult] = useState<RoomResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [debug, setDebug] = useState(false);

  const handleCreateRoom = async () => {
    setLoading(true);
    setResult(null);

    try {
      const res = await window.ipcRenderer.invoke("create-room", {
        serverUrl,
        username,
        roomCode: roomCode || undefined,
        debug,
      });

      setResult(res);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setResult({
        error: `Failed to create room: ${errorMessage}`,
        stderr: "IPC communication error",
      });
    } finally {
      setLoading(false);
    }
  };

  const generateRoomCode = () => {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    let result = "";
    for (let i = 0; i < 6; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setRoomCode(result);
  };

  return (
    <div
      style={{
        padding: "20px",
        fontFamily: "Arial",
        maxWidth: "600px",
        margin: "0 auto",
      }}
    >
      <h1 style={{ textAlign: "center", color: "#333" }}>P2P Room Creator</h1>

      <div
        style={{
          backgroundColor: "#fff",
          padding: "20px",
          borderRadius: "8px",
          boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
          marginBottom: "20px",
        }}
      >
        <div style={{ marginBottom: "15px" }}>
          <label
            style={{
              display: "block",
              marginBottom: "5px",
              fontWeight: "bold",
            }}
          >
            Server URL:
          </label>
          <input
            type="text"
            value={serverUrl}
            onChange={(e) => setServerUrl(e.target.value)}
            style={{
              width: "100%",
              padding: "10px",
              border: "1px solid #ddd",
              borderRadius: "4px",
            }}
            placeholder="http://localhost:5000"
          />
        </div>

        <div style={{ marginBottom: "15px" }}>
          <label
            style={{
              display: "block",
              marginBottom: "5px",
              fontWeight: "bold",
            }}
          >
            Room Code:
          </label>
          <div style={{ display: "flex", gap: "10px" }}>
            <input
              type="text"
              value={roomCode}
              onChange={(e) => setRoomCode(e.target.value)}
              style={{
                flex: 1,
                padding: "10px",
                border: "1px solid #ddd",
                borderRadius: "4px",
              }}
              placeholder="Leave empty to generate"
            />
            <button
              onClick={generateRoomCode}
              style={{
                padding: "10px 15px",
                backgroundColor: "#f0f0f0",
                border: "1px solid #ddd",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Generate
            </button>
          </div>
        </div>

        <div style={{ marginBottom: "15px" }}>
          <label
            style={{
              display: "block",
              marginBottom: "5px",
              fontWeight: "bold",
            }}
          >
            Username:
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{
              width: "100%",
              padding: "10px",
              border: "1px solid #ddd",
              borderRadius: "4px",
            }}
            placeholder="Your username"
          />
        </div>

        <div
          style={{
            marginBottom: "20px",
            display: "flex",
            alignItems: "center",
          }}
        >
          <input
            type="checkbox"
            id="debug"
            checked={debug}
            onChange={(e) => setDebug(e.target.checked)}
            style={{ marginRight: "8px" }}
          />
          <label htmlFor="debug">Enable debug mode</label>
        </div>

        <button
          onClick={handleCreateRoom}
          disabled={loading || !serverUrl || !username}
          style={{
            width: "100%",
            padding: "12px",
            backgroundColor: loading ? "#cccccc" : "#4CAF50",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: "16px",
          }}
        >
          {loading ? "Creating Room..." : "Create Room"}
        </button>
      </div>

      {result && (
        <div
          style={{
            backgroundColor: "#fff",
            padding: "20px",
            borderRadius: "8px",
            boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
          }}
        >
          <h3>Result:</h3>

          {result.error ? (
            <div
              style={{
                color: "red",
                padding: "10px",
                backgroundColor: "#ffebee",
                borderRadius: "4px",
              }}
            >
              ❌ Error: {result.error}
            </div>
          ) : (
            <div
              style={{
                padding: "10px",
                backgroundColor: "#e8f5e9",
                borderRadius: "4px",
              }}
            >
              <div>✅ Success!</div>
              <div>Status: {result.status}</div>
              {result.room_code && (
                <div>
                  Room Code: <code>{result.room_code}</code>
                </div>
              )}
              {result.my_ip && (
                <div>
                  Your IP: <code>{result.my_ip}</code>
                </div>
              )}
              {result.my_port && (
                <div>
                  Your Port: <code>{result.my_port}</code>
                </div>
              )}
              {result.message && <div>{result.message}</div>}
            </div>
          )}

          {result.stderr && (
            <details style={{ marginTop: "15px" }}>
              <summary style={{ cursor: "pointer", fontWeight: "bold" }}>
                Error Output
              </summary>
              <pre
                style={{
                  backgroundColor: "#fff3f3",
                  padding: "10px",
                  borderRadius: "4px",
                  overflowX: "auto",
                  fontSize: "12px",
                  color: "darksalmon",
                }}
              >
                {result.stderr}
              </pre>
            </details>
          )}

          {result.rawOutput && (
            <details style={{ marginTop: "15px" }}>
              <summary style={{ cursor: "pointer", fontWeight: "bold" }}>
                Raw Python Output
              </summary>
              <pre
                style={{
                  backgroundColor: "#f5f5f5",
                  padding: "10px",
                  borderRadius: "4px",
                  overflowX: "auto",
                  fontSize: "12px",
                }}
              >
                {result.rawOutput}
              </pre>
            </details>
          )}
        </div>
      )}

      <div
        style={{
          marginTop: "30px",
          fontSize: "14px",
          color: "#666",
          textAlign: "center",
        }}
      >
        <p>Share the room code with others so they can join your room.</p>
        <p>
          Once the room is created, others can join using the same server URL
          and room code.
        </p>
      </div>
    </div>
  );
}

export default App;
