const { default: makeWASocket, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const pino = require('pino');

async function send() {
    const { state, saveCreds } = await useMultiFileAuthState('./whatsapp_session');
    const sock = makeWASocket({ 
        auth: state,
        logger: pino({ level: 'silent' })
    });
    
    sock.ev.on('connection.update', async (update) => {
        const { connection, qr } = update;
        if (qr) console.log('QR Code generated. You need to scan first!');
        if (connection === 'open') {
            console.log('CONNECTED! Sending test message...');
            const target = '03147139674@s.whatsapp.net';
            await sock.sendMessage(target, { text: '🤖 JARVIS TEST: System is Alive!' });
            console.log('MESSAGE SENT to ' + target);
            process.exit(0);
        }
        if (connection === 'close') {
            console.log('Connection closed.');
        }
    });
}
send().catch(err => console.error(err));
