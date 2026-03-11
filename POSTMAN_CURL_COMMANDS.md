# NoaVoice LiveKit Backend - Complete API Documentation

**Base URL:** `http://localhost:8000/api/v1` (for local development)  
**Swagger UI:** `http://localhost:8000/docs`  
**ReDoc:** `http://localhost:8000/redoc`  
**API Version:** v1  
**Last Updated:** March 11, 2026

---

## Quick Navigation
- [Authentication Endpoints](#authentication-endpoints)
- [Agent Endpoints](#agent-endpoints)
- [Agent Actions/Tools Endpoints](#agent-actiontools-endpoints)
- [Knowledge Base Endpoints](#knowledge-base-endpoints)
- [Appointments Endpoints](#appointments-endpoints)
- [Pipecat Agent Endpoints](#pipecat-agent-endpoints)
- [Twilio Endpoints](#twilio-endpoints)
- [Testing Endpoints](#testing-endpoints)

---

## Authentication Endpoints

### 1. Register (Create New User)
**Endpoint:** `POST /auth/register`  
**Status:** ✅ Active  
**Rate Limit:** 3 requests/minute per IP  
**Authentication:** None  
**Response Code:** 201 Created

#### Request Body
```json
{
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

#### Password Requirements
- ✅ Minimum 8 characters
- ✅ At least 1 uppercase letter (A-Z)
- ✅ At least 1 digit (0-9)
- Special characters recommended

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

#### Success Response (201 Created)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "picture": null,
  "provider": "local",
  "is_verified": false,
  "created_at": "2026-03-11T08:42:33.011000Z",
  "last_login": null
}
```

#### Error Response (409 - Email Already Exists)
```json
{
  "detail": "Email already registered"
}
```

---

### 2. Login (Local Authentication)
**Endpoint:** `POST /auth/login`  
**Status:** ✅ Active  
**Rate Limit:** 5 requests/minute per IP  
**Authentication:** None  
**Response Code:** 200 OK

#### Request Body
```json
{
  "email": "john.doe@example.com",
  "password": "SecurePass123!"
}
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123!"
  }'
```

#### Success Response (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3NDE2MDQ1NTMsImlhdCI6MTc0MTYwMzY1M30.ABC123XYZ",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3NDIyMDg0NTN9.DEF456UVW",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### Token Details
- **access_token:** Valid for 15 minutes (900 seconds)
- **refresh_token:** Valid for 7 days
- **Usage:** Include `access_token` in Authorization header for authenticated requests

---

### 3. Refresh Access Token
**Endpoint:** `POST /auth/refresh`  
**Status:** ✅ Active  
**Rate Limit:** 10 requests/minute per IP  
**Authentication:** None  
**Response Code:** 200 OK

#### Request Body
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

#### Success Response (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### Security Notes
- ⚠️ Old refresh token is immediately invalidated (token rotation)
- ⚠️ If a stolen/reused token is detected, ALL sessions are revoked

---

### 4. Logout (Revoke Refresh Token)
**Endpoint:** `POST /auth/logout`  
**Status:** ✅ Active  
**Authentication:** None  
**Response Code:** 204 No Content

#### Request Body
```json
{
  "refresh_token": "YOUR_REFRESH_TOKEN"
}
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

#### Success Response
```
(204 No Content - empty body)
```

---

### 5. Google OAuth Login
**Endpoint:** `GET /auth/google`  
**Status:** ✅ Active  
**Rate Limit:** 20 requests/minute per IP  
**Authentication:** None  
**Response Code:** 302 Redirect

#### Purpose
Initiates Google OAuth 2.0 flow. Redirects browser to Google's consent screen.

#### Browser Usage
```javascript
// In your React/Vue/Angular app
window.location.href = "http://localhost:8000/api/v1/auth/google";
```

---

### 6. Get Current User Info
**Endpoint:** `GET /auth/me`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 200 OK

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Success Response (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "picture": "https://example.com/avatar.jpg",
  "provider": "local",
  "is_verified": true,
  "created_at": "2026-03-07T08:42:33.011000Z",
  "last_login": "2026-03-11T10:15:22.000000Z"
}
```

---

## Agent Endpoints

### 1. Create New Agent
**Endpoint:** `POST /agents`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 201 Created

#### Request Body
```json
{
  "name": "Customer Support Agent",
  "description": "AI agent to handle customer support inquiries"
}
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/agents" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Support Agent",
    "description": "AI agent to handle customer support inquiries"
  }'
```

#### Success Response (201 Created)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Customer Support Agent",
  "description": "AI agent to handle customer support inquiries",
  "voice": "",
  "language": "EN",
  "timezone": "America/Detroit",
  "system_prompt": "",
  "first_message": "",
  "end_call_message": "",
  "voicemail_message": "",
  "first_message_mode": "assistant-speaks-first",
  "end_call_function_enabled": true,
  "recording_enabled": false,
  "detect_caller_number": false,
  "multi_lingual_enabled": false,
  "is_active": true,
  "created_at": "2026-03-11T08:42:33.011000Z",
  "updated_at": "2026-03-11T08:42:33.011000Z"
}
```

---

### 2. List All Agents (Paginated)
**Endpoint:** `GET /agents`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 200 OK

#### Query Parameters
| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| skip | integer | 0 | - | Number of records to skip (pagination offset) |
| limit | integer | 20 | 100 | Number of records to return per page |

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/agents?skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Success Response (200 OK)
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Customer Support Agent",
      "description": "AI agent to handle customer support inquiries",
      "voice": "Xb7hH8MSUJpSbSDYk0k2",
      "is_active": true,
      "created_at": "2026-03-07T08:42:33.011000Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### 3. Search Agents
**Endpoint:** `GET /agents/search`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 200 OK

#### Query Parameters
| Parameter | Type | Required | Min Length | Description |
|-----------|------|----------|-----------|-------------|
| q | string | Yes | 1 | Search term (searches name and description) |

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/agents/search?q=support" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 4. Get Agent Details
**Endpoint:** `GET /agents/{agent_id}`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 200 OK

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 5. Update Agent
**Endpoint:** `PUT /agents/{agent_id}`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 200 OK

#### Request Body (All fields optional)
```json
{
  "name": "Updated Agent Name",
  "description": "Updated description",
  "voice": "Xb7hH8MSUJpSbSDYk0k3",
  "is_active": true
}
```

#### cURL Example
```bash
curl -X PUT "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Agent Name"
  }'
```

---

### 6. Delete Agent
**Endpoint:** `DELETE /agents/{agent_id}`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 204 No Content

#### cURL Example
```bash
curl -X DELETE "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Note
Soft delete: Agent is marked as deleted but data is preserved in database

---

### 7. Get Available Tools
**Endpoint:** `GET /agents/tools/available`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 200 OK

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/agents/tools/available" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Success Response (200 OK)
```json
[
  {
    "id": "tool-001",
    "tool_key": "cal_com_appointment",
    "display_name": "Cal.com Appointment Booking",
    "category": "appointment",
    "description": "Book and manage appointments using Cal.com"
  }
]
```

---

## Agent Actions/Tools Endpoints

### 1. Add Tool to Agent
**Endpoint:** `POST /agents/{agent_id}/actions`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 201 Created

#### Request Body
```json
{
  "tool_id": "tool-001",
  "custom_name": "Appointment Booking",
  "start_message": "Let me check available slots for you",
  "complete_message": "Your appointment has been confirmed",
  "failed_message": "I couldn't complete the booking"
}
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000/actions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "tool-001",
    "custom_name": "Appointment Booking"
  }'
```

---

### 2. Update Agent Action
**Endpoint:** `PUT /agents/{agent_id}/actions/{action_id}`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 200 OK

#### Request Body (All fields optional)
```json
{
  "custom_name": "Updated Name"
}
```

---

### 3. Remove Action from Agent
**Endpoint:** `DELETE /agents/{agent_id}/actions/{action_id}`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 204 No Content

---

## Knowledge Base Endpoints

### 1. List User's Knowledge Bases
**Endpoint:** `GET /agents/knowledge-bases`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 200 OK

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/agents/knowledge-bases?skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 2. Upload Knowledge Base Document
**Endpoint:** `POST /agents/knowledge-bases/upload`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 201 Created
**File Limit:** 10 MB
**Supported Types:** PDF, TXT, DOCX, XLSX

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/agents/knowledge-bases/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F "document_name=Product Manual"
```

---

### 3. Assign Knowledge Base to Agent
**Endpoint:** `POST /agents/{agent_id}/knowledge-bases`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 201 Created

#### Request Body
```json
{
  "knowledge_base_id": "kb-001"
}
```

---

### 4. Remove Knowledge Base from Agent
**Endpoint:** `DELETE /agents/{agent_id}/knowledge-bases/{kb_id}`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 204 No Content

---

### 5. Delete Knowledge Base
**Endpoint:** `DELETE /agents/knowledge-bases/{kb_id}`  
**Status:** ✅ Active  
**Authentication:** ✅ Required (Bearer token)  
**Response Code:** 204 No Content

---

## Appointments Endpoints

### 1. Get Available Appointment Slots
**Endpoint:** `GET /appointments/available-slots`  
**Status:** ✅ Active  
**Authentication:** None  
**Response Code:** 200 OK

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| date | string | Yes | Date in YYYY-MM-DD format |
| timezone | string | No | Timezone (default: Asia/Kolkata) |

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/appointments/available-slots?date=2026-03-15&timezone=America/New_York"
```

---

### 2. Book Appointment
**Endpoint:** `POST /appointments/book`  
**Status:** ✅ Active  
**Authentication:** None  
**Response Code:** 201 Created

#### Request Body
```json
{
  "datetime_natural": "tomorrow at 3pm",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "timezone": "America/New_York",
  "notes": "First time patient"
}
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/appointments/book" \
  -H "Content-Type: application/json" \
  -d '{
    "datetime_natural": "tomorrow at 3pm",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "timezone": "America/New_York"
  }'
```

---

### 3. Get Booking Details
**Endpoint:** `GET /appointments/booking`  
**Status:** ✅ Active  
**Authentication:** None  
**Response Code:** 200 OK

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | Patient email address |

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/appointments/booking?email=john@example.com"
```

---

### 4. Reschedule Appointment
**Endpoint:** `POST /appointments/reschedule`  
**Status:** ✅ Active  
**Authentication:** None  
**Response Code:** 200 OK

#### Request Body
```json
{
  "email": "john@example.com",
  "new_start": "next Friday at 10am",
  "reason": "Conflict with other meeting",
  "timezone": "America/New_York"
}
```

---

### 5. Cancel Appointment
**Endpoint:** `POST /appointments/cancel`  
**Status:** ✅ Active  
**Authentication:** None  
**Response Code:** 200 OK

#### Request Body
```json
{
  "email": "john@example.com",
  "reason": "No longer need the appointment"
}
```

---

## Pipecat Agent Endpoints

### 1. Check Agent Health
**Endpoint:** `GET /api/agent/health`  
**Status:** ✅ Active  
**Authentication:** None  
**Response Code:** 200 OK

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/api/agent/health"
```

#### Success Response
```json
{
  "status": "ok",
  "agent_reachable": true
}
```

---

### 2. Connect to Agent
**Endpoint:** `POST /api/agent/connect`  
**Status:** ✅ Active  
**Authentication:** None  
**Response Code:** 200 OK

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/api/agent/connect"
```

#### Success Response
```json
{
  "rtc_url": "http://localhost:7860/api/offer",
  "agent_url": "http://localhost:7860",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Twilio Endpoints

### 1. Make Outbound Call
**Endpoint:** `POST /twilio/voice/call`  
**Status:** ✅ Active  
**Authentication:** None  
**Response Code:** 200 OK

#### Request Body
```
to: +1234567890
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/twilio/voice/call" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "to=%2B1234567890"
```

---

### 2. Send SMS
**Endpoint:** `POST /twilio/sms/send`  
**Status:** ✅ Active  
**Authentication:** None  
**Response Code:** 200 OK

#### Request Body
```
to: +1234567890
body: Hello, this is a test message
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/twilio/sms/send" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "to=%2B1234567890&body=Hello%20world"
```

---

## Testing Endpoints

### 1. Redis Test
**Endpoint:** `GET /api/redis/redis-test`  
**Status:** ✅ Active  
**Authentication:** None  
**Response Code:** 200 OK

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/redis/redis-test"
```

---

## System Health

### Health Check
**Endpoint:** `GET /health`  
**Status:** ✅ Active  
**Response Code:** 200 OK

#### cURL Example
```bash
curl -X GET "http://localhost:8000/health"
```

---

## Standard Error Codes

| Status Code | Meaning |
|-------------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 413 | Payload Too Large |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## Authentication

Include Bearer token in Authorization header:

```bash
curl -X GET "http://localhost:8000/api/v1/agents" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

**Last Updated:** March 11, 2026
