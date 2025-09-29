import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Copy, RefreshCw, LogIn, PlusCircle } from "lucide-react";

// Simple toast implementation
const useToast = () => {
  return {
    toast: (options: { title: string; description?: string; variant?: string }) => {
      console.log("Toast:", options.title, options.description);
    }
  };
};

// Simple cn utility
const cn = (...classes: (string | undefined)[]) => {
  return classes.filter(Boolean).join(' ');
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

const MainPage = () => {
  const { toast } = useToast();
  const [serverUrl, setServerUrl] = useState("https://signalingserverdomain.download");
  const [roomCode, setRoomCode] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isCreatingRoom, setIsCreatingRoom] = useState(true);
  const [result, setResult] = useState<RoomResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [debug, setDebug] = useState(false);
  const [currentView, setCurrentView] = useState<"form" | "result">("form");

  const handleRoomAction = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const action = isCreatingRoom ? "create-room" : "join-room";
      const res = await window.ipcRenderer.invoke(action, {
        serverUrl,
        username,
        roomCode: roomCode || undefined,
        password: password || undefined,
        create: isCreatingRoom,
        debug,
      });

      setResult(res);
      setCurrentView("result");
      
      toast({
        title: isCreatingRoom ? "Room created!" : "Joined room!",
        description: isCreatingRoom 
          ? "Share the room code with others to join"
          : `Successfully joined ${roomCode}`,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
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
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-4 md:p-8">
      <div className="max-w-2xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Secure P2P Chat</h1>
          <p className="text-gray-600">End-to-end encrypted peer-to-peer communication</p>
        </header>

        {currentView === "form" ? (
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
                          <RefreshCw className={cn("w-4 h-4 mr-2", loading ? "animate-spin" : "")} />
                          Generate
                        </Button>
                      </div>
                      <Input
                        id="roomCode"
                        value={roomCode}
                        onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
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
                        onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
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
                      placeholder={isCreatingRoom ? "Set a password (optional)" : "Enter room password"}
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
                        onClick={() => setServerUrl(prev => 
                          prev === "https://signalingserverdomain.download" 
                            ? "http://localhost:5000" 
                            : "https://signalingserverdomain.download"
                        )}
                        className="text-blue-600 hover:underline"
                      >
                        {serverUrl.includes("localhost") ? "Use Production Server" : "Use Local Server"}
                      </button>
                    </div>
                  </div>
                </div>
              </CardContent>
              
              <CardFooter className="flex flex-col space-y-2">
                <Button 
                  type="submit" 
                  className="w-full"
                  disabled={loading || !username || (!isCreatingRoom && !roomCode)}
                >
                  {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isCreatingRoom ? "Create Room" : "Join Room"}
                </Button>
                
                <div className="text-sm text-muted-foreground text-center">
                  {isCreatingRoom 
                    ? "You'll be able to invite others after creation"
                    : "Make sure you have the correct room code and password"}
                </div>
              </CardFooter>
            </form>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Room Ready!</span>
                <span className="font-mono bg-primary/10 px-3 py-1 rounded-md text-primary">
                  {roomCode}
                </span>
              </CardTitle>
              <CardDescription>
                {isCreatingRoom 
                  ? "Share the room details with others to join"
                  : "You've successfully joined the room!"}
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <div className="bg-muted/50 p-4 rounded-lg">
                <h4 className="font-medium mb-2">Connection Details</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Server:</span>
                    <div className="flex items-center">
                      <code className="text-sm bg-background px-2 py-1 rounded">
                        {serverUrl}
                      </code>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => copyToClipboard(serverUrl)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Room Code:</span>
                    <div className="flex items-center">
                      <code className="font-mono text-sm bg-background px-2 py-1 rounded">
                        {roomCode}
                      </code>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => copyToClipboard(roomCode)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  
                  {password && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Password:</span>
                      <div className="flex items-center">
                        <code className="font-mono text-sm bg-background px-2 py-1 rounded">
                          {password.replace(/./g, '•')}
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
              
              {result?.my_ip && (
                <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg border border-green-200 dark:border-green-800">
                  <h4 className="font-medium text-green-800 dark:text-green-200 mb-2">Direct Connection</h4>
                  <p className="text-sm text-green-700 dark:text-green-300 mb-2">
                    Your direct connection details (for advanced users):
                  </p>
                  <div className="space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-green-800/80 dark:text-green-200/80">IP Address:</span>
                      <code className="font-mono text-sm bg-green-100 dark:bg-green-900/50 px-2 py-1 rounded">
                        {result.my_ip}
                      </code>
                    </div>
                    {result.my_port && (
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-green-800/80 dark:text-green-200/80">Port:</span>
                        <code className="font-mono text-sm bg-green-100 dark:bg-green-900/50 px-2 py-1 rounded">
                          {result.my_port}
                        </code>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {result?.error && (
                <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg border border-red-200 dark:border-red-800">
                  <h4 className="font-medium text-red-800 dark:text-red-200">Error</h4>
                  <p className="text-sm text-red-700 dark:text-red-300">{result.error}</p>
                  {result.stderr && (
                    <pre className="mt-2 p-2 bg-red-100 dark:bg-red-900/30 text-xs text-red-800 dark:text-red-200 rounded overflow-auto max-h-32">
                      {result.stderr}
                    </pre>
                  )}
                </div>
              )}
            </CardContent>
            
            <CardFooter className="flex justify-between">
              <Button
                variant="outline"
                onClick={resetForm}
              >
                Back
              </Button>
              <div className="space-x-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    const shareText = `Join my secure chat room!\n\nRoom Code: ${roomCode}\nServer: ${serverUrl}`;
                    copyToClipboard(shareText);
                  }}
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copy Invite
                </Button>
                <Button
                  onClick={() => {
                    // TODO: Implement chat view
                    console.log("Opening chat...");
                  }}
                >
                  Open Chat
                </Button>
              </div>
            </CardFooter>
          </Card>
        )}
      </div>
    </div>
  );
};

export default MainPage;
