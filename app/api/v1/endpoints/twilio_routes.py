import os
import asyncio
from fastapi import APIRouter, Form, Request, Response, HTTPException
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/twilio", tags=["twilio"])

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN  = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE       = os.environ["TWILIO_PHONE_NUMBER"]
BASE_URL           = os.environ["BASE_URL"]

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# ──────────────────────────────────────────
# VOICE: Incoming call webhook (Twilio hits this)
# ──────────────────────────────────────────
@router.post("/voice/incoming")
async def incoming_call():
    """
    Twilio voice webhook — incoming call handler.
    
    **Description:**
    Twilio calls this webhook when someone dials your number.
    We respond with TwiML to stream audio to Pipecat via WebSocket.
    
    **Response:** Returns TwiML XML that instructs Twilio to:
    - Connect the call to a WebSocket stream
    - Keep the connection alive while the WS session processes the call
    
    **Status:** 200 OK
    """
    response = VoiceResponse()
    connect = Connect()
    # Point to your Pipecat WebSocket endpoint
    connect.stream(url=f"wss://{BASE_URL.replace('https://', '')}/pipecat/ws")
    response.append(connect)
    response.pause(length=60)  # Keep call alive while WS runs
    return Response(content=str(response), media_type="application/xml")


# ──────────────────────────────────────────
# VOICE: Make an outbound call
# ──────────────────────────────────────────
@router.post("/voice/call")
async def make_call(to: str = Form(...)):
    """
    Make an outbound voice call.
    
    **Description:**
    Called from React UI to initiate an outbound call via Twilio.
    
    **Parameters:**
    - **to** (required): Phone number to call (must be in E.164 format, e.g., "+1234567890")
    
    **Response:**
    - **status**: "initiated" - Call has been queued with Twilio
    - **call_sid**: Twilio Call Session ID for tracking
    
    **Example Response:**
    ```json
    {
        "status": "initiated",
        "call_sid": "CA1234567890abcdef1234567890abcdef"
    }
    ```
    
    **Status:** 200 OK
    """
    call = twilio_client.calls.create(
        to=to,
        from_=TWILIO_PHONE,
        url=f"{BASE_URL}/twilio/voice/incoming",  # TwiML instructions
    )
    return {"status": "initiated", "call_sid": call.sid}


# ──────────────────────────────────────────
# SMS: Send outbound SMS
# ──────────────────────────────────────────
@router.post("/sms/send")
async def send_sms(to: str = Form(...), body: str = Form(...)):
    """
    Send outbound SMS message.
    
    **Description:**
    Called from React UI to send an SMS via Twilio.
    
    **Parameters:**
    - **to** (required): Phone number to send SMS to (E.164 format, e.g., "+1234567890")
    - **body** (required): Message content (max 160 characters for single SMS)
    
    **Response:**
    - **status**: "sent" - SMS has been queued with Twilio
    - **message_sid**: Twilio Message Session ID for tracking
    
    **Example Response:**
    ```json
    {
        "status": "sent",
        "message_sid": "SM1234567890abcdef1234567890abcdef"
    }
    ```
    
    **Status:** 200 OK
    """
    message = twilio_client.messages.create(
        to=to,
        from_=TWILIO_PHONE,
        body=body,
    )
    return {"status": "sent", "message_sid": message.sid}


# ──────────────────────────────────────────
# SMS: Receive incoming SMS (webhook)
# ──────────────────────────────────────────
@router.post("/sms/incoming")
async def incoming_sms(
    From: str = Form(...),
    Body: str = Form(...),
):
    """
    Twilio SMS webhook — incoming SMS handler.
    
    **Description:**
    Twilio calls this webhook when someone texts your number.
    We return a TwiML reply to confirm receipt.
    
    **Parameters (auto-populated by Twilio):**
    - **From**: Sender's phone number (E.164 format)
    - **Body**: Message content
    
    **Response:** Returns TwiML XML with an auto-reply message
    
    **Status:** 200 OK
    """
    print(f"📨 SMS from {From}: {Body}")

    # Auto-reply
    response = MessagingResponse()
    response.message(f"Thanks! You said: {Body}")

    return Response(content=str(response), media_type="application/xml")


# ──────────────────────────────────────────
# STATUS CALLBACK
# ──────────────────────────────────────────
@router.post("/status")
async def call_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
):
    """
    Twilio status callback — call state change notification.
    
    **Description:**
    Twilio calls this webhook to notify about call state changes:
    - Initiated, Ringing, In-progress, Completed, Canceled, Failed
    
    **Parameters (auto-populated by Twilio):**
    - **CallSid**: Unique call identifier
    - **CallStatus**: Current call status
    
    **Response:**
    - **received**: true - Webhook successfully processed
    
    **Example Response:**
    ```json
    {
        "received": true
    }
    ```
    
    **Status:** 200 OK
    """