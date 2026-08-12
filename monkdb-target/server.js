import express from 'express';
import { spawn } from 'child_process';

const app = express();
app.use(express.json());

console.log("Booting MonkDB SDK Sub-Process...");

// 1. Spawn their official SDK as a background process
const mcpProcess = spawn('node', [
    '-e',
    "import('@monkdb/monkdb-mcp').then(m => m.startMonkDBMCPServer())"
]);

let sseResponse = null;

// 2. HTTP GET /sse -> The Handshake
app.get('/sse', (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    sseResponse = res;
    
    // Per MCP Spec: Tell the client where to POST messages
    res.write(`event: endpoint\ndata: /messages\n\n`);
    console.log("SSE Connection Established.");
});

// 3. Pipe their Stdio Output -> SSE Network Stream
mcpProcess.stdout.on('data', (data) => {
    if (sseResponse) {
        // MCP Stdio outputs newline-delimited JSON
        const lines = data.toString().split('\n').filter(line => line.trim());
        for (const line of lines) {
            sseResponse.write(`event: message\ndata: ${line}\n\n`);
        }
    }
});

mcpProcess.stderr.on('data', (data) => {
    console.error(`[MonkDB SDK Log]: ${data}`);
});

// 4. Pipe Network POST -> Their Stdio Input
app.post('/messages', (req, res) => {
    const payload = JSON.stringify(req.body) + '\n';
    mcpProcess.stdin.write(payload);
    res.sendStatus(202);
});

app.listen(8000, '0.0.0.0', () => {
    console.log("Aegis L7 Stdio-to-HTTP Bridge running on port 8000");
});