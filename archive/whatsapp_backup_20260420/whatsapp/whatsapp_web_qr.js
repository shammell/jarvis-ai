// WhatsApp Bridge with Web-based QR Code Display
const { default: makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const express = require('express');
const QRCode = require('qrcode');
const pino = require('pino');

const app = express();
const PORT = 3001;

let qrCodeData = null;
let connectionStatus = 'Initializing...';

const logger = pino({ level: 'silent' }); // Suppress logs

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('../whatsapp_session');

    const sock = makeWASocket({
        auth: state,
        logger: logger,
        browser: ['JARVIS v9.0', 'Chrome', '10.0'],
    });

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log('\n📱 QR Code generated! Open browser at: http://localhost:3001');
            qrCodeData = qr;
            connectionStatus = 'QR Code Ready - Scan with WhatsApp';
        }

        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error instanceof Boom)
                ? lastDisconnect.error.output.statusCode !== DisconnectReason.loggedOut
                : true;

            connectionStatus = 'Connection closed';
            console.log('Connection closed. Reconnecting:', shouldReconnect);

            if (shouldReconnect) {
                setTimeout(() => connectToWhatsApp(), 3000);
            }
        } else if (connection === 'open') {
            console.log('\n✅ WhatsApp Connected Successfully!');
            connectionStatus = 'Connected ✅';
            qrCodeData = null;
        }
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type === 'notify') {
            for (const msg of messages) {
                if (!msg.key.fromMe && msg.message) {
                    const from = msg.key.remoteJid;
                    const text = msg.message.conversation ||
                                msg.message.extendedTextMessage?.text || '';

                    console.log(`\n📨 Message from ${from}: ${text}`);

                    if (text.toLowerCase().includes('jarvis')) {
                        await sock.sendMessage(from, {
                            text: '🤖 JARVIS v9.0 ULTRA is online! How can I help you?'
                        });
                    }
                }
            }
        }
    });

    return sock;
}

// Web interface
app.get('/', async (req, res) => {
    if (qrCodeData) {
        try {
            const qrImage = await QRCode.toDataURL(qrCodeData);
            res.send(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>JARVIS WhatsApp QR Code</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            min-height: 100vh;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            margin: 0;
                        }
                        .container {
                            background: rgba(255, 255, 255, 0.1);
                            padding: 40px;
                            border-radius: 20px;
                            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                            backdrop-filter: blur(4px);
                            border: 1px solid rgba(255, 255, 255, 0.18);
                            text-align: center;
                        }
                        h1 { margin-top: 0; font-size: 2.5em; }
                        .qr-code {
                            background: white;
                            padding: 20px;
                            border-radius: 10px;
                            margin: 20px 0;
                        }
                        .instructions {
                            font-size: 1.2em;
                            margin: 20px 0;
                        }
                        .status {
                            background: rgba(0, 255, 0, 0.2);
                            padding: 10px 20px;
                            border-radius: 5px;
                            margin-top: 20px;
                        }
                    </style>
                    <meta http-equiv="refresh" content="5">
                </head>
                <body>
                    <div class="container">
                        <h1>🤖 JARVIS WhatsApp Connection</h1>
                        <div class="instructions">
                            📱 Open WhatsApp on your phone<br>
                            ⚙️ Go to Settings → Linked Devices<br>
                            📷 Tap "Link a Device"<br>
                            🔍 Scan this QR code
                        </div>
                        <div class="qr-code">
                            <img src="${qrImage}" alt="QR Code" style="width: 300px; height: 300px;">
                        </div>
                        <div class="status">Status: ${connectionStatus}</div>
                        <p style="font-size: 0.9em; opacity: 0.8;">Page auto-refreshes every 5 seconds</p>
                    </div>
                </body>
                </html>
            `);
        } catch (err) {
            res.send(`<h1>Error generating QR code: ${err.message}</h1>`);
        }
    } else {
        res.send(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>JARVIS WhatsApp Status</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        margin: 0;
                    }
                    .container {
                        background: rgba(255, 255, 255, 0.1);
                        padding: 40px;
                        border-radius: 20px;
                        text-align: center;
                    }
                </style>
                <meta http-equiv="refresh" content="3">
            </head>
            <body>
                <div class="container">
                    <h1>🤖 JARVIS WhatsApp</h1>
                    <h2>Status: ${connectionStatus}</h2>
                    <p>Waiting for QR code...</p>
                </div>
            </body>
            </html>
        `);
    }
});

app.listen(PORT, () => {
    console.log('==============================================');
    console.log('🚀 JARVIS WhatsApp Bridge Starting...');
    console.log(`📱 Open browser at: http://localhost:${PORT}`);
    console.log('==============================================\n');
    connectToWhatsApp();
});
