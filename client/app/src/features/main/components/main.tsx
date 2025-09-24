import React, { useState } from "react";
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
};

export default MainPage;
