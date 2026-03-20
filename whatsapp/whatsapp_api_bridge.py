"""
WhatsApp API Bridge for JARVIS
Connects JARVIS to existing WhatsApp Web session
Phone: 03147139674 (Shameel profile)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import logging

app = FastAPI(title="JARVIS WhatsApp Bridge", version="1.0.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Message queue for incoming/outgoing messages
message_queue = []
outgoing_queue = []

class WhatsAppMessage(BaseModel):
    phone: str
    message: str
    sender: Optional[str] = None

class MessageResponse(BaseModel):
    success: bool
    message: str
    message_id: Optional[str] = None

@app.post("/api/whatsapp/send")
async def send_message(msg: WhatsAppMessage):
    """
    Send a WhatsApp message
    """
    try:
        # Add to outgoing queue
        outgoing_queue.append({
            "phone": msg.phone,
            "message": msg.message,
            "timestamp": "2026-03-09T09:10:29.021Z"
        })

        logger.info(f"📤 Queued message to {msg.phone}: {msg.message}")

        return MessageResponse(
            success=True,
            message="Message queued for sending",
            message_id=f"msg_{len(outgoing_queue)}"
        )
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/whatsapp/messages")
async def get_messages():
    """
    Get received WhatsApp messages
    """
    return {
        "success": True,
        "messages": message_queue,
        "count": len(message_queue)
    }

@app.get("/api/whatsapp/outgoing")
async def get_outgoing():
    """
    Get messages waiting to be sent
    """
    return {
        "success": True,
        "messages": outgoing_queue,
        "count": len(outgoing_queue)
    }

@app.post("/api/whatsapp/receive")
async def receive_message(msg: WhatsAppMessage):
    """
    Receive a WhatsApp message (called by browser extension/script)
    """
    try:
        message_queue.append({
            "phone": msg.phone,
            "message": msg.message,
            "sender": msg.sender,
            "timestamp": "2026-03-09T09:10:29.021Z"
        })

        logger.info(f"📥 Received message from {msg.phone}: {msg.message}")

        # Auto-respond if message contains "jarvis"
        if "jarvis" in msg.message.lower():
            outgoing_queue.append({
                "phone": msg.phone,
                "message": "🤖 JARVIS v9.0 ULTRA is online! How can I help you?",
                "timestamp": "2026-03-09T09:10:29.021Z"
            })

        return MessageResponse(
            success=True,
            message="Message received"
        )
    except Exception as e:
        logger.error(f"Error receiving message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/whatsapp/status")
async def get_status():
    """
    Get WhatsApp connection status
    """
    return {
        "connected": True,
        "phone": "03147139674",
        "profile": "Shameel",
        "messages_received": len(message_queue),
        "messages_pending": len(outgoing_queue)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "WhatsApp Bridge",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 JARVIS WhatsApp API Bridge Starting...")
    logger.info("📱 Phone: 03147139674 (Shameel profile)")
    logger.info("🌐 API: http://localhost:3002")
    logger.info("=" * 50)

    uvicorn.run(app, host="0.0.0.0", port=3002, log_level="info")
