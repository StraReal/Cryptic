import { ipcMain } from "electron";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

ipcMain.handle(
  "create-room",
  async (event, { serverUrl, username, roomCode, debug = false }) => {
    const scriptPath = path.join(process.cwd(), "..", "test", "peer_room.py");

    // Validate inputs
    if (!serverUrl || !username) {
      return { error: "Missing server URL or username" };
    }

    console.log(
      `[Electron] Creating room with server: ${serverUrl}, username: ${username}`
    );

    // Prepare arguments
    const args = ["--server-url", serverUrl, "--username", username];

    if (roomCode) {
      args.push("--room-code", roomCode);
    }

    if (debug) {
      args.push("--debug");
    }

    // Spawn Python process
    const pythonProcess = spawn("python3", [scriptPath, ...args]);

    let output = "";
    let errorOutput = "";

    // Collect stdout output
    pythonProcess.stdout.on("data", (data) => {
      const text = data.toString();
      output += text;

      // If debug mode, log to console
      if (debug) {
        console.log(`[Python stdout] ${text.trim()}`);
      }
    });

    // Collect stderr output
    pythonProcess.stderr.on("data", (data) => {
      const text = data.toString();
      errorOutput += text;
      console.error(`[Python stderr] ${text.trim()}`);
    });

    // When Python finishes
    return new Promise((resolve) => {
      pythonProcess.on("close", (code) => {
        console.log(`[Python] Process exited with code ${code}`);

        try {
          if (!output.trim()) {
            resolve({
              error: "No output from Python script",
              stderr: errorOutput,
            });
            return;
          }

          // Try to parse the output as JSON
          const result = JSON.parse(output.trim());
          resolve(result);
        } catch (err) {
          console.error("Failed to parse Python output:", err);
          resolve({
            error: "Invalid response from Python. Expected JSON.",
            rawOutput: output,
            stderr: errorOutput,
          });
        }
      });

      // If Python crashes or doesn't respond in 15 seconds
      setTimeout(() => {
        if (!pythonProcess.killed) {
          pythonProcess.kill();
          resolve({
            error: "Python script timed out. Server may be down.",
            stderr: errorOutput,
          });
        }
      }, 15000);
    });
  }
);
