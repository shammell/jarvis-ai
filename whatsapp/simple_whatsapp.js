// Simple WhatsApp Bridge for QR Code Scanning
const { default: makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const qrcode = require('qrcode-terminal');
const pino = require('pino');

const logger = pino({ level: 'info' });

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('../whatsapp_session');

    const sock = makeWASocket({
        auth: state,
        logger: logger,
        browser: ['JARVIS v9.0', 'Chrome', '10.0'],
    });

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log('\n==============================================');
            console.log('📱 SCAN THIS QR CODE WITH YOUR WHATSAPP APP');
            console.log('==============================================\n');
            qrcode.generate(qr, { small: true });
        }

        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error instanceof Boom)
                ? lastDisconnect.error.output.statusCode !== DisconnectReason.loggedOut
                : true;

            console.log('Connection closed. Reconnecting:', shouldReconnect);

            if (shouldReconnect) {
                connectToWhatsApp();
            }
        } else if (connection === 'open') {
            console.log('\n✅ WhatsApp Connected Successfully!');
            console.log('✅ You can now send and receive messages');
            console.log('✅ Session saved for future use\n');
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

                    console.log(`\n📨 Message from ${from}:`);
                    console.log(`   ${text}`);

                    // Auto-reply for testing
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

console.log('==============================================');
console.log('🚀 JARVIS WhatsApp Bridge Starting...');
console.log('==============================================\n');

connectToWhatsApp().catch(err => {
    console.error('Error connecting to WhatsApp:', err);
    process.exit(1);
});
