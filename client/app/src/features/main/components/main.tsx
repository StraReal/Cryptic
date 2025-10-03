import React, { useState, useEffect, useRef } from "react";
import { ChatRoom } from "./ChatRoom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Loader2, Copy, RefreshCw, LogIn, PlusCircle } from "lucide-react";

// Simple toast implementation since useToast is not available
const useToast = () => {
  return {
    toast: (options: {
      title: string;
      description?: string;
      variant?: string;
    }) => {
      console.log("Toast:", options.title, options.description);
    },
  };
};

// Simple cn utility since it's not available
const cn = (...classes: (string | undefined)[]) => {
  return classes.filter(Boolean).join(" ");
};

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

const toWebSocketUrl = (url: string) => {
  const [scheme, rest] = url.split("://");
  const wsScheme = scheme === "https" ? "wss" : "ws";
  return `${wsScheme}://${rest.replace(/\/$/, "")}/ws`;
};

const useWebSocket = (serverUrl: string, onMessage: (data: any) => void) => {
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    return () => {
      socketRef.current?.close();
    };
  }, []);

  const connect = () => {
    return new Promise<void>((resolve, reject) => {
      try {
        // Always use the production server URL
        const finalServerUrl = serverUrl;
        const wsUrl = toWebSocketUrl(finalServerUrl);

        console.log("Attempting to connect to:", wsUrl);
        console.log("Original server URL:", finalServerUrl);

        const ws = new WebSocket(wsUrl);
        socketRef.current = ws;

        ws.onopen = () => {
          console.log("WebSocket connected successfully to:", wsUrl);
          resolve();
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log("Received WebSocket message:", data);
            onMessage(data);
          } catch (e) {
            console.error("Failed to parse WebSocket message:", event.data);
          }
        };

        ws.onerror = (error) => {
          console.error("WebSocket error details:", {
            error,
            url: wsUrl,
            readyState: ws.readyState,
            protocol: ws.protocol,
            extensions: ws.extensions,
          });
          reject(
            new Error(
              `WebSocket connection failed to ${wsUrl}. Check console for details.`
            )
          );
        };

        ws.onclose = (event) => {
          console.log("WebSocket disconnected:", {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean,
            url: wsUrl,
          });
        };
      } catch (error) {
        console.error("Error creating WebSocket:", error);
        reject(error);
      }
    });
  };

  const sendMessage = (payload: object) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(payload));
    } else {
      console.error("WebSocket is not connected.");
    }
  };

  return { connect, sendMessage };
};

const MainPage = () => {
  const { toast } = useToast();
  const [serverUrl, setServerUrl] = useState("http://localhost:5001");
  const [roomCode, setRoomCode] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isCreatingRoom, setIsCreatingRoom] = useState(true);
  const [result, setResult] = useState<RoomResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [debug, setDebug] = useState(false);
  const [currentView, setCurrentView] = useState<"form" | "result" | "chat">(
    "form"
  );
  const [messages, setMessages] = useState<any[]>([]);

  const handleServerMessage = (data: any) => {
    setLoading(false);
    switch (data.type) {
      case "created":
        setResult({ status: "room_created", room_code: data.room });
        setCurrentView("chat");
        toast({
          title: "Room Created!",
          description: "Share the room code with others to join.",
        });
        break;
      case "joined":
        setResult({
          status: "room_joined",
          room_code: data.room,
          message: `Host: ${data.user}`,
        });
        setCurrentView("chat");
        toast({
          title: "Joined Room!",
          description: `Successfully joined room ${data.room}.`,
        });
        break;
      case "error":
        setResult({ error: data.message });
        setCurrentView("result"); // Show error on the result page
        toast({
          title: "Error",
          description: data.message,
          variant: "destructive",
        });
        break;
      case "message":
        // Add message to the messages array
        const newMessage = {
          id: data.id,
          text: data.text,
          sender: data.sender,
          timestamp: data.timestamp,
        };
        setMessages((prev) => {
          // Avoid duplicates by checking if message with same ID already exists
          if (prev.some((msg) => msg.id === newMessage.id)) {
            return prev;
          }
          return [...prev, newMessage];
        });
        break;
      default:
        console.log("Unhandled message type:", data.type);
    }
  };

  const { connect, sendMessage } = useWebSocket(serverUrl, handleServerMessage);

  const handleRoomAction = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      await connect();
      sendMessage({
        type: "join",
        room: roomCode,
        from: username,
        password: password,
        create: isCreatingRoom,
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Unknown error during connection";
      toast({
        title: "Connection Error",
        description: errorMessage,
        variant: "destructive",
      });
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
    toast({
      title: "Room code generated",
      description: "A new room code has been created",
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied to clipboard!",
      description: `${text} has been copied to your clipboard`,
    });
  };

  const resetForm = () => {
    setCurrentView("form");
    setRoomCode("");
    setResult(null);
    setMessages([]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-4 md:p-8">
      <div className="max-w-2xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Cryptic
          </h1>
          <p className="text-gray-600">
            End-to-end encrypted peer-to-peer chat
          </p>
        </header>

        {currentView === "chat" ? (
          <ChatRoom
            roomCode={result?.room_code || roomCode}
            username={username}
            onLeave={resetForm}
            sendMessage={sendMessage}
            messages={messages}
          />
        ) : currentView === "form" ? (
          <Card className="w-full">
            <CardHeader>
              <CardTitle className="text-2xl">
                {isCreatingRoom ? "Create a New Room" : "Join Existing Room"}
              </CardTitle>
              <CardDescription>
                {isCreatingRoom
                  ? "Set up a new secure chat room and invite others to join"
                  : "Enter the room details to join an existing chat"}
              </CardDescription>
            </CardHeader>

            <form onSubmit={handleRoomAction}>
              <CardContent className="space-y-4">
                <div className="flex space-x-4 mb-4">
                  <Button
                    type="button"
                    variant={isCreatingRoom ? "default" : "outline"}
                    className="flex-1"
                    onClick={() => setIsCreatingRoom(true)}
                  >
                    <PlusCircle className="w-4 h-4 mr-2" />
                    Create Room
                  </Button>
                  <Button
                    type="button"
                    variant={!isCreatingRoom ? "default" : "outline"}
                    className="flex-1"
                    onClick={() => setIsCreatingRoom(false)}
                  >
                    <LogIn className="w-4 h-4 mr-2" />
                    Join Room
                  </Button>
                </div>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="username">Your Name</Label>
                    <Input
                      id="username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="Enter your name"
                      required
                    />
                  </div>

                  {isCreatingRoom && (
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <Label htmlFor="roomCode">Room Code</Label>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={generateRoomCode}
                          disabled={loading}
                        >
                          <RefreshCw
                            className={cn(
                              "w-4 h-4 mr-2",
                              loading ? "animate-spin" : ""
                            )}
                          />
                          Generate
                        </Button>
                      </div>
                      <Input
                        id="roomCode"
                        value={roomCode}
                        onChange={(e) =>
                          setRoomCode(e.target.value.toUpperCase())
                        }
                        placeholder="Leave empty to generate"
                        className="font-mono"
                        maxLength={6}
                      />
                    </div>
                  )}

                  {!isCreatingRoom && (
                    <div>
                      <Label htmlFor="joinRoomCode">Room Code</Label>
                      <Input
                        id="joinRoomCode"
                        value={roomCode}
                        onChange={(e) =>
                          setRoomCode(e.target.value.toUpperCase())
                        }
                        placeholder="Enter room code"
                        className="font-mono uppercase"
                        required={!isCreatingRoom}
                        maxLength={6}
                      />
                    </div>
                  )}

                  <div>
                    <Label htmlFor="password">
                      Password {!isCreatingRoom && "(if required)"}
                    </Label>
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={
                        isCreatingRoom
                          ? "Set a password (optional)"
                          : "Enter room password"
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="debug-mode"
                        checked={debug}
                        onChange={(e) => setDebug(e.target.checked)}
                        className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <Label htmlFor="debug-mode">Debug Mode</Label>
                    </div>

                    <div className="text-sm text-muted-foreground">
                      <button
                        type="button"
                        onClick={() =>
                          setServerUrl((prev) =>
                            prev === "http://localhost:5001"
                              ? "https://signalingserverdomain.download"
                              : "http://localhost:5001"
                          )
                        }
                        className="text-blue-600 hover:underline"
                      >
                        {serverUrl.includes("localhost")
                          ? "Use Production Server"
                          : "Use Local Server"}
                      </button>
                      <span className="ml-2 text-gray-500">({serverUrl})</span>
                    </div>
                  </div>
                </div>
              </CardContent>

              <CardFooter className="flex flex-col space-y-2">
                <Button
                  type="submit"
                  className="w-full"
                  disabled={
                    loading || !username || (!isCreatingRoom && !roomCode)
                  }
                >
                  {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isCreatingRoom ? "Create Room" : "Join Room"}
                </Button>
              </CardFooter>
            </form>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Room Ready!</span>
                <span className="font-mono bg-primary/10 px-3 py-1 rounded-md text-primary">
                  {result?.room_code || roomCode}
                </span>
              </CardTitle>
              <CardDescription>
                {isCreatingRoom
                  ? "Share the room details with others to join"
                  : "You've successfully joined the room!"}
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              {result?.error ? (
                <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg border border-red-200 dark:border-red-800">
                  <h4 className="font-medium text-red-800 dark:text-red-200">
                    Error
                  </h4>
                  <p className="text-sm text-red-700 dark:text-red-300">
                    {result.error}
                  </p>
                  {result.stderr && (
                    <pre className="mt-2 p-2 bg-red-100 dark:bg-red-900/30 text-xs text-red-800 dark:text-red-200 rounded overflow-auto max-h-32">
                      {result.stderr}
                    </pre>
                  )}
                </div>
              ) : (
                <div className="bg-muted/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Connection Details</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">
                        Room Code:
                      </span>
                      <div className="flex items-center">
                        <code className="font-mono text-sm bg-background px-2 py-1 rounded">
                          {result?.room_code || roomCode}
                        </code>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() =>
                            copyToClipboard(result?.room_code || roomCode)
                          }
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    {password && (
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">
                          Password:
                        </span>
                        <div className="flex items-center">
                          <code className="font-mono text-sm bg-background px-2 py-1 rounded">
                            {"*".repeat(password.length)}
                          </code>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => copyToClipboard(password)}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {debug && result?.rawOutput && (
                <div className="bg-gray-100 dark:bg-gray-800/50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Raw Output</h4>
                  <pre className="mt-2 p-2 bg-gray-200 dark:bg-gray-900/30 text-xs rounded overflow-auto max-h-40">
                    {result.rawOutput}
                  </pre>
                </div>
              )}
            </CardContent>

            <CardFooter className="flex justify-start">
              <Button variant="outline" onClick={resetForm}>
                Back
              </Button>
            </CardFooter>
          </Card>
        )}
      </div>
    </div>
  );
};

export default MainPage;
