// ==========================================================
// JARVIS v9.0 - Baileys WhatsApp Bridge (Lightweight)
// Replaces Puppeteer with WebSocket-based connection
// Expected RAM: 500MB → 30MB (94% reduction)
// ==========================================================

const { default: makeWASocket, DisconnectReason, useMultiFileAuthState, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const express = require('express');
const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');
const pino = require('pino');

const qrcode = require('qrcode-terminal');

// ==========================================================
// PhD-Level Enhancement: gRPC Integration with Circuit Breaker
// ==========================================================
const JarvisGRPCClient = require('../grpc/node_client.js');

// Circuit Breaker State Machine
class CircuitBreaker {
    constructor(threshold = 5, timeout = 60000) {
        this.failureCount = 0;
        this.threshold = threshold;
        this.timeout = timeout;
        this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
        this.nextAttempt = Date.now();
    }

    async execute(fn) {
        if (this.state === 'OPEN') {
            if (Date.now() < this.nextAttempt) {
                throw new Error('Circuit breaker is OPEN');
            }
            this.state = 'HALF_OPEN';
        }

        try {
            const result = await fn();
            this.onSuccess();
            return result;
        } catch (error) {
            this.onFailure();
            throw error;
        }
    }

    onSuccess() {
        this.failureCount = 0;
        this.state = 'CLOSED';
    }

    onFailure() {
        this.failureCount++;
        if (this.failureCount >= this.threshold) {
            this.state = 'OPEN';
            this.nextAttempt = Date.now() + this.timeout;
            logger.error(`Circuit breaker opened after ${this.failureCount} failures`);
        }
    }

    getState() {
        return this.state;
    }
}

// Initialize gRPC client with circuit breaker
let grpcClient = null;
let circuitBreaker = new CircuitBreaker(5, 60000);
let grpcHealthy = false;

async function initGRPCClient() {
    try {
        grpcClient = new JarvisGRPCClient('localhost:50051');
        const health = await grpcClient.healthCheck();
        grpcHealthy = health.healthy;
        logger.info('✅ gRPC client connected to Python backend');
        return true;
    } catch (error) {
        logger.error({ error }, '❌ gRPC client initialization failed');
        grpcHealthy = false;
        return false;
    }
}

// Configuration
const CONFIG = {
    PORT: process.env.WHATSAPP_PORT || 3000,
    JWT_SECRET: process.env.JWT_SECRET,
    AUTH_DIR: './whatsapp_session',
    RATE_LIMIT_WINDOW: 60000, // 1 minute
    RATE_LIMIT_MAX: 30, // 30 requests per minute
    LOG_LEVEL: process.env.LOG_LEVEL || 'info'
};

if (!CONFIG.JWT_SECRET) {
    throw new Error('JWT_SECRET is required. Refusing to start with insecure default.');
}

// Logger
const logger = pino({ level: CONFIG.LOG_LEVEL });

// Global socket instance
let sock = null;
let isConnected = false;
let messageQueue = [];
let deduplicationCache = new Map(); // Message deduplication
let currentQRCode = null; // Store current QR code

// Express app
const app = express();
app.use(express.json());

// Rate limiting
const limiter = rateLimit({
    windowMs: CONFIG.RATE_LIMIT_WINDOW,
    max: CONFIG.RATE_LIMIT_MAX,
    message: { error: 'Too many requests, please try again later' }
});
app.use('/api/', limiter);

// JWT Authentication Middleware
function authenticateJWT(req, res, next) {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) {
        return res.status(401).json({ error: 'No token provided' });
    }

    jwt.verify(token, CONFIG.JWT_SECRET, (err, user) => {
        if (err) {
            return res.status(403).json({ error: 'Invalid token' });
        }
        req.user = user;
        next();
    });
}

// Message deduplication
function isDuplicate(messageId) {
    if (deduplicationCache.has(messageId)) {
        return true;
    }
    deduplicationCache.set(messageId, Date.now());

    // Cleanup old entries (older than 5 minutes)
    if (deduplicationCache.size > 1000) {
        const fiveMinutesAgo = Date.now() - 300000;
        for (const [id, timestamp] of deduplicationCache.entries()) {
            if (timestamp < fiveMinutesAgo) {
                deduplicationCache.delete(id);
            }
        }
    }
    return false;
}

// Initialize WhatsApp connection
async function connectToWhatsApp() {
    const { version, isLatest } = await fetchLatestBaileysVersion();
    logger.info('Using WA version v' + version.join('.'));
    const { state, saveCreds } = await useMultiFileAuthState(CONFIG.AUTH_DIR);

    sock = makeWASocket({
        version,
        auth: state,
        logger: pino({ level: 'silent' }), // Reduce Baileys logs
        // using default browser // Standard browser sig prevents instant drops
        syncFullHistory: false,
        generateHighQualityLinkPreview: true,
        markOnlineOnConnect: true
    });

    // Connection updates
    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            logger.info('Generating new QR Code...');
            currentQRCode = qr; // Store QR code for web display
            qrcode.generate(qr, { small: true });
            logger.info('Scan the above QR code with WhatsApp');
            logger.info('QR code also available at http://localhost:3000/qr');
        }

        if (connection === 'close') {
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

            logger.warn({ reason: lastDisconnect?.error?.message, statusCode }, 'Connection closed');
            isConnected = false;

            if (shouldReconnect) {
                logger.info('Reconnecting in 5 seconds...');
                setTimeout(connectToWhatsApp, 5000);
            } else {
                logger.error('Logged out from WhatsApp. Please delete the session folder and re-scan.');
            }
        } else if (connection === 'open') {
            logger.info('WhatsApp connection established');
            isConnected = true;
            processMessageQueue();
        }
    });

    // Save credentials on update
    sock.ev.on('creds.update', saveCreds);

    // Incoming messages
    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        logger.info({ type, messageCount: messages.length }, '📨 Messages event received');

        if (type !== 'notify') {
            logger.info({ type }, '⏭️ Skipping non-notify message type');
            return;
        }

        for (const msg of messages) {
            logger.info({ fromMe: msg.key.fromMe, hasMessage: !!msg.message }, '🔍 Checking message');

            if (!msg.message || msg.key.fromMe) {
                logger.info('⏭️ Skipping message (no content or from self)');
                continue;
            }

            // Deduplication
            if (isDuplicate(msg.key.id)) {
                logger.info('⏭️ Skipping duplicate message');
                continue;
            }

            const from = msg.key.remoteJid;
            const text = msg.message.conversation
                || msg.message.extendedTextMessage?.text
                || '';

            logger.info({ from, text, textLength: text.length }, '📝 Message content extracted');

            if (text) {
                metrics.messagesReceived++;
                const startTime = Date.now();

                logger.info({ from, text }, '✅ Received message');

                // Forward to Python backend (gRPC)
                try {
                    await forwardToPython({ from, text, messageId: msg.key.id });
                    metrics.messagesForwarded++;

                    const latency = Date.now() - startTime;
                    updateMetrics(true, latency);
                } catch (error) {
                    metrics.messagesFailed++;
                    updateMetrics(false, Date.now() - startTime);
                    logger.error({ error }, 'Failed to forward message to Python');
                }
            }
        }
    });
}

// ==========================================================
// PhD-Level Enhancement: Resilient gRPC Communication
// Features: Exponential backoff, circuit breaker, fallback
// ==========================================================
async function forwardToPython(data) {
    const maxRetries = 3;
    let lastError = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            // Check circuit breaker state
            if (circuitBreaker.getState() === 'OPEN') {
                logger.warn('Circuit breaker OPEN, skipping gRPC call');
                throw new Error('Circuit breaker is OPEN');
            }

            // Execute with circuit breaker protection
            const result = await circuitBreaker.execute(async () => {
                if (!grpcClient) {
                    await initGRPCClient();
                }

                logger.info({ from: data.from, messageId: data.messageId }, '📤 Forwarding to Python via gRPC');

                const response = await grpcClient.processMessage(
                    data.from,
                    data.text,
                    data.messageId
                );

                if (!response.success) {
                    throw new Error(response.error || 'Python processing failed');
                }

                logger.info({
                    processingTime: response.processing_time_ms,
                    messageId: data.messageId
                }, '✅ Python response received');

                // Send response back to WhatsApp
                if (response.response_text && sock && isConnected) {
                    await sendMessageDirect(data.from, response.response_text);
                }

                return response;
            });

            return result;

        } catch (error) {
            lastError = error;
            logger.error({
                error: error.message,
                attempt,
                maxRetries,
                circuitState: circuitBreaker.getState()
            }, '❌ gRPC call failed');

            if (attempt < maxRetries) {
                // Exponential backoff: 1s, 2s, 4s
                const backoffMs = Math.pow(2, attempt - 1) * 1000;
                logger.info({ backoffMs }, '⏳ Retrying with exponential backoff...');
                await new Promise(resolve => setTimeout(resolve, backoffMs));
            }
        }
    }

    // All retries failed - send error message to user
    logger.error({ error: lastError.message }, '💥 All retry attempts exhausted');

    if (sock && isConnected) {
        await sendMessageDirect(
            data.from,
            '⚠️ JARVIS is temporarily unavailable. Please try again in a moment.'
        );
    }

    throw lastError;
}

// Process queued messages
async function processMessageQueue() {
    while (messageQueue.length > 0 && isConnected) {
        const { to, message, resolve, reject } = messageQueue.shift();
        try {
            await sendMessageDirect(to, message);
            resolve({ success: true });
        } catch (error) {
            reject(error);
        }
    }
}

// Send message directly
async function sendMessageDirect(to, message) {
    if (!sock) throw new Error('Socket not initialized');

    const jid = to.includes('@') ? to : `${to}@s.whatsapp.net`;
    await sock.sendMessage(jid, { text: message });
    logger.info({ to: jid, message }, 'Message sent');
}

// ==========================================================
// PhD-Level Enhancement: Health Monitoring & Metrics
// ==========================================================
const metrics = {
    messagesReceived: 0,
    messagesForwarded: 0,
    messagesFailed: 0,
    grpcCallsSucceeded: 0,
    grpcCallsFailed: 0,
    circuitBreakerTrips: 0,
    averageLatency: 0,
    startTime: Date.now()
};

function updateMetrics(success, latency) {
    if (success) {
        metrics.grpcCallsSucceeded++;
    } else {
        metrics.grpcCallsFailed++;
    }

    // Exponential moving average for latency
    metrics.averageLatency = metrics.averageLatency * 0.9 + latency * 0.1;
}

// API Routes

// Enhanced health endpoint with detailed metrics
app.get('/health', (req, res) => {
    const uptime = Date.now() - metrics.startTime;
    const memUsage = process.memoryUsage();

    res.json({
        status: isConnected ? 'connected' : 'disconnected',
        grpc: {
            healthy: grpcHealthy,
            circuitBreaker: circuitBreaker.getState(),
            successRate: metrics.grpcCallsSucceeded / (metrics.grpcCallsSucceeded + metrics.grpcCallsFailed) || 0
        },
        metrics: {
            ...metrics,
            uptime,
            uptimeHuman: `${Math.floor(uptime / 3600000)}h ${Math.floor((uptime % 3600000) / 60000)}m`
        },
        memory: {
            heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
            heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
            rss: Math.round(memUsage.rss / 1024 / 1024)
        },
        queueSize: messageQueue.length
    });
});

// QR Code endpoint - returns HTML page with QR code
app.get('/qr', (req, res) => {
    if (!currentQRCode) {
        return res.status(503).send(`
<!DOCTYPE html>
<html>
<head>
    <title>JARVIS WhatsApp QR Code</title>
    <style>
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .container { text-align: center; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
        h1 { color: #333; margin: 0 0 20px 0; }
        .status { color: #ff6b6b; font-size: 18px; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄 JARVIS WhatsApp Bridge</h1>
        <div class="spinner"></div>
        <p class="status">Generating QR Code...</p>
        <p>Please wait, the QR code will appear shortly.</p>
        <script>
            setTimeout(() => location.reload(), 2000);
        </script>
    </div>
</body>
</html>
        `);
    }

    const qrHtml = `
<!DOCTYPE html>
<html>
<head>
    <title>JARVIS WhatsApp QR Code</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .container { text-align: center; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 500px; }
        h1 { color: #333; margin: 0 0 10px 0; font-size: 28px; }
        .subtitle { color: #666; margin: 0 0 30px 0; font-size: 14px; }
        #qrcode { display: flex; justify-content: center; margin: 30px 0; }
        .instructions { background: #f0f4ff; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: left; }
        .instructions h3 { margin: 0 0 10px 0; color: #667eea; }
        .instructions ol { margin: 0; padding-left: 20px; }
        .instructions li { margin: 8px 0; color: #555; }
        .status { padding: 15px; background: #e8f5e9; border-left: 4px solid #4caf50; border-radius: 4px; margin: 20px 0; color: #2e7d32; }
        .refresh { margin-top: 20px; }
        button { background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 14px; }
        button:hover { background: #764ba2; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 JARVIS WhatsApp Bridge</h1>
        <p class="subtitle">Scan QR Code to Connect</p>

        <div id="qrcode"></div>

        <div class="status">
            ✅ System Ready - Waiting for WhatsApp Connection
        </div>

        <div class="instructions">
            <h3>How to Connect:</h3>
            <ol>
                <li>Open WhatsApp on your phone</li>
                <li>Go to Settings → Linked Devices</li>
                <li>Tap "Link a Device"</li>
                <li>Point your phone at the QR code above</li>
                <li>Wait for connection confirmation</li>
            </ol>
        </div>

        <div class="refresh">
            <button onclick="location.reload()">🔄 Refresh QR Code</button>
        </div>
    </div>

    <script>
        const qrData = '${currentQRCode}';
        new QRCode(document.getElementById('qrcode'), {
            text: qrData,
            width: 300,
            height: 300,
            colorDark: '#000000',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.H
        });
    </script>
</body>
</html>
    `;

    res.set('Content-Type', 'text/html; charset=utf-8');
    res.send(qrHtml);
});

// Metrics endpoint for Prometheus/Grafana
app.get('/metrics', (req, res) => {
    const promMetrics = `
# HELP jarvis_messages_received_total Total messages received from WhatsApp
# TYPE jarvis_messages_received_total counter
jarvis_messages_received_total ${metrics.messagesReceived}

# HELP jarvis_messages_forwarded_total Total messages forwarded to Python
# TYPE jarvis_messages_forwarded_total counter
jarvis_messages_forwarded_total ${metrics.messagesForwarded}

# HELP jarvis_grpc_calls_succeeded_total Total successful gRPC calls
# TYPE jarvis_grpc_calls_succeeded_total counter
jarvis_grpc_calls_succeeded_total ${metrics.grpcCallsSucceeded}

# HELP jarvis_grpc_calls_failed_total Total failed gRPC calls
# TYPE jarvis_grpc_calls_failed_total counter
jarvis_grpc_calls_failed_total ${metrics.grpcCallsFailed}

# HELP jarvis_average_latency_ms Average message processing latency
# TYPE jarvis_average_latency_ms gauge
jarvis_average_latency_ms ${metrics.averageLatency.toFixed(2)}

# HELP jarvis_circuit_breaker_state Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN)
# TYPE jarvis_circuit_breaker_state gauge
jarvis_circuit_breaker_state ${circuitBreaker.getState() === 'CLOSED' ? 0 : circuitBreaker.getState() === 'HALF_OPEN' ? 1 : 2}
`;
    res.set('Content-Type', 'text/plain');
    res.send(promMetrics);
});

// Send message
app.post('/api/send', authenticateJWT, async (req, res) => {
    const { to, message } = req.body;

    if (!to || !message) {
        return res.status(400).json({ error: 'Missing to or message' });
    }

    if (!isConnected) {
        // Queue message
        return new Promise((resolve, reject) => {
            messageQueue.push({ to, message, resolve, reject });
            res.json({ success: true, queued: true });
        });
    }

    try {
        await sendMessageDirect(to, message);
        res.json({ success: true });
    } catch (error) {
        logger.error({ error }, 'Failed to send message');
        res.status(500).json({ error: error.message });
    }
});

// Get connection status
app.get('/api/status', authenticateJWT, (req, res) => {
    res.json({
        connected: isConnected,
        queueSize: messageQueue.length
    });
});

// Generate JWT token (for testing)
app.post('/api/auth/token', (req, res) => {
    const { username, password } = req.body;

    // Simple auth (replace with proper auth in production)
    if (username === 'jarvis' && password === process.env.ADMIN_PASSWORD) {
        const token = jwt.sign({ username }, CONFIG.JWT_SECRET, { expiresIn: '24h' });
        res.json({ token });
    } else {
        res.status(401).json({ error: 'Invalid credentials' });
    }
});

// Start server with gRPC initialization
async function start() {
    try {
        // Initialize gRPC client first
        logger.info('🔌 Initializing gRPC connection...');
        await initGRPCClient();

        // Start WhatsApp connection
        await connectToWhatsApp();

        app.listen(CONFIG.PORT, () => {
            logger.info(`✅ Baileys WhatsApp Bridge running on port ${CONFIG.PORT}`);
            logger.info(`📊 Memory usage: ${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)}MB`);
            logger.info(`🔗 gRPC status: ${grpcHealthy ? 'Connected' : 'Disconnected'}`);
            logger.info(`🔄 Circuit breaker: ${circuitBreaker.getState()}`);
        });

        // Periodic health check for gRPC
        setInterval(async () => {
            if (grpcClient) {
                try {
                    await grpcClient.healthCheck();
                    grpcHealthy = true;
                } catch (error) {
                    grpcHealthy = false;
                    logger.warn('⚠️ gRPC health check failed');
                }
            }
        }, 30000); // Every 30 seconds

    } catch (error) {
        logger.error({ error }, 'Failed to start bridge');
        process.exit(1);
    }
}

// Graceful shutdown
process.on('SIGINT', async () => {
    logger.info('Shutting down gracefully...');
    if (sock) {
        await sock.logout();
    }
    process.exit(0);
});

// Start
start();
