# NoaVoice LiveKit Backend - API Documentation & Examples

**Base URL:** `http://localhost:8000/api/v1` (for local development)  
**API Version:** v1  
**Last Updated:** March 7, 2026

---

## Table of Contents
1. [Authentication Endpoints](#authentication-endpoints)
2. [Agent Endpoints](#agent-endpoints)
3. [Appointments Endpoints](#appointments-endpoints)
4. [Error Handling](#error-handling)
5. [Helper Scripts](#helper-scripts)

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
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 digit
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

#### Response Example (Success - 201)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "auth_provider": "local",
  "is_active": true,
  "created_at": "2026-03-07T08:42:33.011Z",
  "updated_at": "2026-03-07T08:42:33.011Z"
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

#### Response Example (Success - 200)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3NDE2MDQ1NTMsImlhdCI6MTc0MTYwMzY1M30.ABC123XYZ",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3NDIyMDg0NTN9.DEF456UVW",
  "expires_in": 900
}
```

#### Token Details
- **access_token:** Valid for 15 minutes (900 seconds)
- **refresh_token:** Valid for 7 days
- Use `access_token` in Authorization header for authenticated requests

#### Error Response (401 - Invalid Credentials)
```json
{
  "detail": "Invalid email or password"
}
```

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

#### Response Example (Success - 200)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3NDE2MDQ1NTN9.NEW_TOKEN_ABC",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3NDIyMDg0NTN9.NEW_REFRESH_DEF",
  "expires_in": 900
}
```

#### Security Note
- Old refresh token is immediately invalidated (token rotation)
- If stolen/reused token detected, ALL sessions are revoked

---

### 4. Logout (Revoke Refresh Token)
**Endpoint:** `POST /auth/logout`  
**Status:** ✅ Active  
**Rate Limit:** Unlimited  
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

#### Response
No body returned (204 No Content)

---

### 5. Google OAuth Login
**Endpoint:** `GET /auth/google`  
**Status:** ✅ Active  
**Rate Limit:** 20 requests/minute per IP  
**Authentication:** None  
**Response Code:** 302 Redirect

#### Purpose
Initiates Google OAuth 2.0 flow. Redirects browser to Google's consent screen.

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/auth/google" \
  -H "Accept: application/json"
```

#### Browser Usage
```javascript
// In your React/Vue/Angular app
window.location.href = "http://localhost:8000/api/v1/auth/google";
```

#### Security Features
- Generates unique state token (CSRF protection)
- Generates nonce (replay attack prevention)
- Tokens stored in Redis with 5-minute TTL

---

### 6. Google OAuth Callback
**Endpoint:** `GET /auth/google/callback`  
**Status:** ✅ Active  
**Authentication:** None (OAuth callback)  
**Response Code:** 200 OK / Redirect

#### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Authorization code from Google |
| `state` | string | CSRF token for verification |
| `error` | string | Error from Google (if user denies) |

#### cURL Example
```bash
# Typically handled automatically by browser redirects
curl -X GET "http://localhost:8000/api/v1/auth/google/callback?code=4/0ABC123XYZ&state=random_state"
```

#### Response Example (Success)
Redirects to UI with tokens:
```
http://your-frontend-url.com/?access_token=eyJ...&refresh_token=eyJ...
```

---

### 7. Get Current User Info
**Endpoint:** `GET /auth/me`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 200 OK

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example (Success - 200)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "auth_provider": "local",
  "is_active": true,
  "created_at": "2026-03-07T08:42:33.011Z",
  "updated_at": "2026-03-07T08:42:33.011Z"
}
```

#### Error Response (401 - Unauthorized)
```json
{
  "detail": "Invalid or expired token"
}
```



---

## Agent Endpoints

### 1. Create New Agent
**Endpoint:** `POST /agents`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 201 Created

#### Request Body
```json
{
  "name": "Customer Support Agent",
  "description": "AI agent to handle customer support inquiries and issue resolution"
}
```

#### Request Parameters
| Field | Type | Required | Max Length | Description |
|-------|------|----------|-----------|-------------|
| name | string | Yes | 255 | Agent display name |
| description | string | No | 5000 | Agent description |

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

#### Response Example (Success - 201)
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
  "created_at": "2026-03-07T08:42:33.011Z",
  "updated_at": "2026-03-07T08:42:33.011Z"
}
```

#### Auto-populated Default Values
When an agent is created, the following fields are automatically set:
- `voice`: "" (empty string)
- `language`: "EN"
- `timezone`: "America/Detroit"
- `system_prompt`: "" (empty string)
- `first_message`: "" (empty string)
- `end_call_message`: "" (empty string)
- `voicemail_message`: "" (empty string)
- `first_message_mode`: "assistant-speaks-first"
- `end_call_function_enabled`: true
- `recording_enabled`: false
- `detect_caller_number`: false
- `multi_lingual_enabled`: false
- `is_active`: true

---

### 2. List All Agents (Paginated)
**Endpoint:** `GET /agents`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 200 OK

#### Query Parameters
| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| skip | integer | 0 | - | Number of records to skip (pagination offset) |
| limit | integer | 20 | 100 | Number of records to return per page |

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/agents?skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example (Success - 200)
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Customer Support Agent",
      "description": "AI agent to handle customer support inquiries",
      "voice": "Xb7hH8MSUJpSbSDYk0k2",
      "language": "EN",
      "timezone": "America/Detroit",
      "system_prompt": "You are a helpful customer support representative...",
      "first_message": "Hello! How can I help you today?",
      "end_call_message": "Thank you for contacting us!",
      "voicemail_message": "Please leave a message after the beep.",
      "first_message_mode": "assistant-speaks-first",
      "end_call_function_enabled": true,
      "recording_enabled": true,
      "detect_caller_number": false,
      "multi_lingual_enabled": false,
      "is_active": true,
      "created_at": "2026-03-07T08:42:33.011Z",
      "updated_at": "2026-03-07T08:42:33.011Z"
    },
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Appointment Booking Agent",
      "description": "Handles appointment bookings and scheduling",
      "voice": "Xb7hH8MSUJpSbSDYk0k3",
      "language": "EN",
      "timezone": "America/New_York",
      "system_prompt": "You are a professional appointment scheduler...",
      "first_message": "Welcome to our booking system!",
      "end_call_message": "Your appointment has been confirmed.",
      "voicemail_message": "We're currently unavailable.",
      "first_message_mode": "assistant-speaks-first",
      "end_call_function_enabled": true,
      "recording_enabled": true,
      "detect_caller_number": true,
      "multi_lingual_enabled": false,
      "is_active": true,
      "created_at": "2026-03-06T10:22:15.000Z",
      "updated_at": "2026-03-07T08:42:33.011Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### 3. Search Agents
**Endpoint:** `GET /agents/search`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 200 OK

#### Query Parameters
| Parameter | Type | Required | Min Length | Description |
|-----------|------|----------|-----------|-------------|
| q | string | Yes | 1 | Search term (searches name and description) |

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/agents/search?q=support" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example (Success - 200)
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Customer Support Agent",
    "description": "AI agent to handle customer support inquiries",
    "voice": "Xb7hH8MSUJpSbSDYk0k2",
    "language": "EN",
    "timezone": "America/Detroit",
    "system_prompt": "You are a helpful customer support representative...",
    "first_message": "Hello! How can I help you today?",
    "end_call_message": "Thank you for contacting us!",
    "voicemail_message": "Please leave a message after the beep.",
    "first_message_mode": "assistant-speaks-first",
    "end_call_function_enabled": true,
    "recording_enabled": true,
    "detect_caller_number": false,
    "multi_lingual_enabled": false,
    "is_active": true,
    "created_at": "2026-03-07T08:42:33.011Z",
    "updated_at": "2026-03-07T08:42:33.011Z"
  }
]
```

---

### 4. Get Available Tools
**Endpoint:** `GET /agents/tools/available`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 200 OK

#### Purpose
Retrieve list of all available tools/actions that can be assigned to agents.

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/agents/tools/available" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example (Success - 200)
```json
[
  {
    "id": "tool-001",
    "tool_key": "appointment_booking",
    "display_name": "Appointment Booking",
    "category": "appointment",
    "description": "Allow agents to book and manage appointments"
  },
  {
    "id": "tool-002",
    "tool_key": "calendar_sync",
    "display_name": "Calendar Sync",
    "category": "external",
    "description": "Sync appointments with Google Calendar or Outlook"
  },
  {
    "id": "tool-003",
    "tool_key": "sms_notifications",
    "display_name": "SMS Notifications",
    "category": "external",
    "description": "Send SMS notifications to customers"
  }
]
```

---

### 5. Get Agent Details
**Endpoint:** `GET /agents/{agent_id}`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 200 OK

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agent_id | string (UUID) | Yes | The UUID of the agent |

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example (Success - 200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Customer Support Agent",
  "description": "AI agent to handle customer support inquiries",
  "voice": "Xb7hH8MSUJpSbSDYk0k2",
  "language": "EN",
  "timezone": "America/Detroit",
  "system_prompt": "You are a helpful customer support representative. Always be polite and professional.",
  "first_message": "Hello! How can I help you today?",
  "end_call_message": "Thank you for contacting us! Have a great day!",
  "voicemail_message": "Please leave a message after the beep.",
  "first_message_mode": "assistant-speaks-first",
  "end_call_function_enabled": true,
  "recording_enabled": true,
  "detect_caller_number": false,
  "multi_lingual_enabled": false,
  "is_active": true,
  "created_at": "2026-03-07T08:42:33.011Z",
  "updated_at": "2026-03-07T08:42:33.011Z",
  "actions": [
    {
      "id": "action-001",
      "agent_id": "123e4567-e89b-12d3-a456-426614174000",
      "tool_id": "tool-001",
      "tool_key": "appointment_booking",
      "display_name": "Appointment Booking",
      "custom_name": "Book an Appointment",
      "start_message": "Let me help you book an appointment",
      "complete_message": "Your appointment has been successfully booked!",
      "failed_message": "I'm sorry, but I couldn't book the appointment.",
      "is_enabled": true,
      "created_at": "2026-03-07T08:42:33.011Z"
    }
  ],
  "knowledge_bases": [
    {
      "id": "kb-001",
      "document_name": "FAQ Database",
      "file_name": "faq.pdf",
      "file_type": "pdf",
      "file_size": 512000,
      "created_at": "2026-03-07T08:42:33.011Z"
    }
  ],
  "phone": {
    "id": "phone-001",
    "phone_number": "+1-555-0123",
    "is_active": true,
    "created_at": "2026-03-07T08:42:33.011Z"
  }
}
```

#### Error Response (404 - Agent Not Found)
```json
{
  "detail": "Agent not found"
}
```

#### Error Response (403 - Unauthorized)
```json
{
  "detail": "Not authorized to access this agent"
}
```

---

### 6. Update Agent Configuration
**Endpoint:** `PUT /agents/{agent_id}`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 200 OK

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agent_id | string (UUID) | Yes | The UUID of the agent |

#### Request Body (All fields optional)
```json
{
  "name": "Updated Support Agent",
  "description": "Enhanced customer support with AI capabilities",
  "voice": "Xb7hH8MSUJpSbSDYk0k2",
  "language": "EN",
  "timezone": "America/New_York",
  "system_prompt": "You are Maya, a warm and professional customer support representative...",
  "first_message": "Hello! Thank you for calling. How can I assist you today?",
  "end_call_message": "Thank you for calling. Have a wonderful day!",
  "voicemail_message": "Thank you for calling. Please leave your name and number and we'll call you back shortly.",
  "first_message_mode": "assistant-speaks-first",
  "end_call_function_enabled": true,
  "recording_enabled": true,
  "detect_caller_number": true,
  "multi_lingual_enabled": false,
  "is_active": true
}
```

#### Request Parameters
| Field | Type | Max Length | Description |
|-------|------|-----------|-------------|
| name | string | 255 | Agent display name |
| description | string | 5000 | Agent description |
| voice | string | 255 | Voice ID/key for TTS |
| language | string | 10 | Language code (e.g., EN, ES, FR) |
| timezone | string | 100 | Valid timezone string |
| system_prompt | string | unlimited | System prompt for the AI model |
| first_message | string | unlimited | Initial greeting message |
| end_call_message | string | unlimited | Closing message |
| voicemail_message | string | unlimited | Automated voicemail message |
| first_message_mode | string | 50 | How agent initiates calls |
| end_call_function_enabled | boolean | - | Enable end-call callbacks |
| recording_enabled | boolean | - | Enable call recording |
| detect_caller_number | boolean | - | Detect caller's phone number |
| multi_lingual_enabled | boolean | - | Support multiple languages |
| is_active | boolean | - | Agent status |

#### cURL Example (Partial Update)
```bash
curl -X PUT "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "voice": "Xb7hH8MSUJpSbSDYk0k2",
    "system_prompt": "You are Maya, a warm receptionist...",
    "first_message": "Hello, this is Maya. How may I assist you?",
    "timezone": "America/New_York",
    "recording_enabled": true
  }'
```

#### cURL Example (Full Update)
```bash
curl -X PUT "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Support Agent",
    "description": "Enhanced customer support",
    "voice": "Xb7hH8MSUJpSbSDYk0k2",
    "language": "EN",
    "timezone": "America/New_York",
    "system_prompt": "You are Maya, a professional support representative...",
    "first_message": "Hello! How can I help?",
    "end_call_message": "Thank you for calling!",
    "voicemail_message": "Please leave a message.",
    "first_message_mode": "assistant-speaks-first",
    "end_call_function_enabled": true,
    "recording_enabled": true,
    "detect_caller_number": true,
    "multi_lingual_enabled": false,
    "is_active": true
  }'
```

#### Response Example (Success - 200)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Updated Support Agent",
  "description": "Enhanced customer support with AI capabilities",
  "voice": "Xb7hH8MSUJpSbSDYk0k2",
  "language": "EN",
  "timezone": "America/New_York",
  "system_prompt": "You are Maya, a professional support representative...",
  "first_message": "Hello! How can I help?",
  "end_call_message": "Thank you for calling!",
  "voicemail_message": "Please leave a message.",
  "first_message_mode": "assistant-speaks-first",
  "end_call_function_enabled": true,
  "recording_enabled": true,
  "detect_caller_number": true,
  "multi_lingual_enabled": false,
  "is_active": true,
  "created_at": "2026-03-07T08:42:33.011Z",
  "updated_at": "2026-03-07T09:15:22.845Z"
}
```

#### Error Response (404 - Agent Not Found)
```json
{
  "detail": "Agent not found"
}
```

#### Error Response (403 - Unauthorized)
```json
{
  "detail": "Not authorized to access this agent"
}
```

---

### 7. Delete Agent
**Endpoint:** `DELETE /agents/{agent_id}`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 204 No Content

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agent_id | string (UUID) | Yes | The UUID of the agent |

#### cURL Example
```bash
curl -X DELETE "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response
No body returned (204 No Content)

#### Notes
- This is a soft delete (data preserved in database)
- The agent is marked as deleted but can be recovered if needed

#### Error Response (404 - Agent Not Found)
```json
{
  "detail": "Agent not found"
}
```

---

### 8. Add Tool/Action to Agent
**Endpoint:** `POST /agents/{agent_id}/actions`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 201 Created

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agent_id | string (UUID) | Yes | The UUID of the agent |

#### Request Body
```json
{
  "tool_id": "tool-001",
  "custom_name": "Book an Appointment",
  "start_message": "Let me help you schedule an appointment",
  "complete_message": "Your appointment has been successfully booked!",
  "failed_message": "I'm sorry, but I couldn't complete that booking."
}
```

#### Request Parameters
| Field | Type | Required | Max Length | Description |
|-------|------|----------|-----------|-------------|
| tool_id | string | Yes | - | ID of the tool to add |
| custom_name | string | No | 255 | Custom display name for this agent |
| start_message | string | No | - | Message when action begins |
| complete_message | string | No | - | Message on success |
| failed_message | string | No | - | Message on failure |

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000/actions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_id": "tool-001",
    "custom_name": "Book an Appointment",
    "start_message": "Let me help you book an appointment",
    "complete_message": "Your appointment has been confirmed!",
    "failed_message": "I could not book the appointment."
  }'
```

#### Response Example (Success - 201)
```json
{
  "id": "action-001",
  "agent_id": "123e4567-e89b-12d3-a456-426614174000",
  "tool_id": "tool-001",
  "tool_key": "appointment_booking",
  "display_name": "Appointment Booking",
  "custom_name": "Book an Appointment",
  "start_message": "Let me help you book an appointment",
  "complete_message": "Your appointment has been confirmed!",
  "failed_message": "I could not book the appointment.",
  "is_enabled": true,
  "created_at": "2026-03-07T09:15:22.845Z"
}
```

#### Error Response (400 - Tool Already Added)
```json
{
  "detail": "This tool is already assigned to the agent"
}
```

#### Error Response (404 - Tool Not Found)
```json
{
  "detail": "Tool not found"
}
```

---

### 9. Update Action Configuration
**Endpoint:** `PUT /agents/{agent_id}/actions/{action_id}`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 200 OK

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agent_id | string (UUID) | Yes | The UUID of the agent |
| action_id | string (UUID) | Yes | The UUID of the action |

#### Request Body (All fields optional)
```json
{
  "custom_name": "Updated Action Name",
  "start_message": "Updated start message",
  "complete_message": "Updated completion message",
  "failed_message": "Updated failure message",
  "is_enabled": true
}
```

#### cURL Example
```bash
curl -X PUT "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000/actions/action-001" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "custom_name": "Schedule Appointment",
    "start_message": "I can help you schedule an appointment",
    "is_enabled": true
  }'
```

#### Response Example (Success - 200)
```json
{
  "id": "action-001",
  "agent_id": "123e4567-e89b-12d3-a456-426614174000",
  "tool_id": "tool-001",
  "tool_key": "appointment_booking",
  "display_name": "Appointment Booking",
  "custom_name": "Schedule Appointment",
  "start_message": "I can help you schedule an appointment",
  "complete_message": "Your appointment has been confirmed!",
  "failed_message": "I could not book the appointment.",
  "is_enabled": true,
  "created_at": "2026-03-07T09:15:22.845Z"
}
```

---

### 10. Remove Action from Agent
**Endpoint:** `DELETE /agents/{agent_id}/actions/{action_id}`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 204 No Content

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agent_id | string (UUID) | Yes | The UUID of the agent |
| action_id | string (UUID) | Yes | The UUID of the action |

#### cURL Example
```bash
curl -X DELETE "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000/actions/action-001" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response
No body returned (204 No Content)

---

### 11. List User's Knowledge Bases
**Endpoint:** `GET /agents/knowledge-bases`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 200 OK

#### Query Parameters
| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| skip | integer | 0 | - | Number of records to skip |
| limit | integer | 20 | 100 | Number of records to return |

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/agents/knowledge-bases?skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example (Success - 200)
```json
{
  "items": [
    {
      "id": "kb-001-uuid",
      "document_name": "Company FAQ",
      "file_name": "company_faq.pdf",
      "file_type": "pdf",
      "file_size": 1024000,
      "created_at": "2026-03-07T08:42:33.011Z"
    },
    {
      "id": "kb-002-uuid",
      "document_name": "Product Manual",
      "file_name": "product_manual.docx",
      "file_type": "docx",
      "file_size": 2048000,
      "created_at": "2026-03-06T10:22:15.000Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### 12. Upload Knowledge Base
**Endpoint:** `POST /agents/knowledge-bases/upload`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 201 Created

#### Query Parameters
| Parameter | Type | Required | Min Length | Description |
|-----------|------|----------|-----------|-------------|
| document_name | string | Yes | 1 | Display name for the document |

#### Supported File Types
- PDF (.pdf)
- Text files (.txt)
- Word documents (.docx)
- Excel spreadsheets (.xlsx)

#### File Limits
- **Max file size:** 10 MB per file
- **Max files:** No limit per agent

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/agents/knowledge-bases/upload?document_name=Company%20FAQ" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/faq.pdf"
```

#### Response Example (Success - 201)
```json
{
  "id": "kb-001-uuid",
  "document_name": "Company FAQ",
  "file_name": "faq.pdf",
  "file_type": "pdf",
  "file_size": 1024000,
  "created_at": "2026-03-07T09:15:22.845Z"
}
```

#### Error Response (400 - Invalid File Type)
```json
{
  "detail": "File type not allowed. Allowed: pdf, txt, docx, xlsx"
}
```

#### Error Response (413 - File Too Large)
```json
{
  "detail": "File too large. Maximum 10 MB"
}
```

---

### 13. Get Agent's Knowledge Bases
**Endpoint:** `GET /agents/{agent_id}/knowledge-bases`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 200 OK

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agent_id | string (UUID) | Yes | The UUID of the agent |

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000/knowledge-bases" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Accept: application/json"
```

#### Response Example (Success - 200)
```json
[
  {
    "id": "assignment-001",
    "knowledge_base": {
      "id": "kb-001-uuid",
      "document_name": "Company FAQ",
      "file_name": "faq.pdf",
      "file_type": "pdf",
      "file_size": 1024000,
      "created_at": "2026-03-07T08:42:33.011Z"
    },
    "is_enabled": true,
    "created_at": "2026-03-07T09:15:22.845Z"
  }
]
```

---

### 13. Assign Knowledge Base to Agent
**Endpoint:** `POST /agents/{agent_id}/knowledge-bases`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 201 Created

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agent_id | string (UUID) | Yes | The UUID of the agent |

#### Request Body
```json
{
  "knowledge_base_id": "kb-001-uuid"
}
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000/knowledge-bases" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_base_id": "kb-001-uuid"
  }'
```

#### Response Example (Success - 201)
```json
{
  "id": "assignment-001",
  "message": "Knowledge base assigned successfully"
}
```

#### Error Response (400 - Already Assigned)
```json
{
  "detail": "Knowledge base already assigned to this agent"
}
```

#### Error Response (404 - KB Not Found)
```json
{
  "detail": "Knowledge base not found"
}
```

---

### 14. Update Knowledge Base Assignment
**Endpoint:** `PATCH /agents/{agent_id}/knowledge-bases/{kb_id}`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 200 OK

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agent_id | string (UUID) | Yes | The UUID of the agent |
| kb_id | string (UUID) | Yes | The UUID of the knowledge base |

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| is_enabled | boolean | Yes | Enable or disable this KB for the agent |

#### cURL Example (Disable KB)
```bash
curl -X PATCH "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000/knowledge-bases/kb-001-uuid?is_enabled=false" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### cURL Example (Enable KB)
```bash
curl -X PATCH "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000/knowledge-bases/kb-001-uuid?is_enabled=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response Example (Success - 200)
```json
{
  "id": "assignment-001",
  "is_enabled": false,
  "message": "Knowledge base assignment updated"
}
```

---

### 15. Remove Knowledge Base from Agent
**Endpoint:** `DELETE /agents/{agent_id}/knowledge-bases/{kb_id}`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 204 No Content

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| agent_id | string (UUID) | Yes | The UUID of the agent |
| kb_id | string (UUID) | Yes | The UUID of the knowledge base |

#### cURL Example
```bash
curl -X DELETE "http://localhost:8000/api/v1/agents/123e4567-e89b-12d3-a456-426614174000/knowledge-bases/kb-001-uuid" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response
No body returned (204 No Content)

#### Notes
- The knowledge base itself is NOT deleted, only the assignment
- The KB can be reassigned to other agents or the same agent later

---

### 16. Delete Knowledge Base
**Endpoint:** `DELETE /agents/knowledge-bases/{kb_id}`  
**Status:** ✅ Active  
**Authentication:** Required (Bearer token)  
**Response Code:** 204 No Content

#### URL Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| kb_id | string (UUID) | Yes | The UUID of the knowledge base to delete |

#### cURL Example
```bash
curl -X DELETE "http://localhost:8000/api/v1/agents/knowledge-bases/kb-001-uuid" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Response
No body returned (204 No Content)

#### Notes
- User must own the knowledge base (be the original uploader)
- This is a soft delete - the document can be recovered from database if needed
- All assignments (agent-kb relationships) are automatically handled
- Files are retained on disk for potential recovery

#### Error Response (404 - Not Found)
```json
{
  "detail": "Knowledge base not found"
}
```

#### Error Response (403 - Unauthorized)
```json
{
  "detail": "Not authorized to delete this knowledge base"
}
```



---

## Appointments Endpoints

### 1. Get Available Appointment Slots
**Endpoint:** `GET /appointments/available-slots`  
**Status:** ✅ Active  
**Authentication:** Not Required  
**Response Code:** 200 OK

#### Query Parameters
| Parameter | Type | Required | Format | Default | Description |
|-----------|------|----------|--------|---------|-------------|
| date | string | Yes | YYYY-MM-DD | - | Date to check availability |
| timezone | string | No | IANA timezone | Asia/Kolkata | Timezone for slot times |

#### Valid Timezone Examples
- America/New_York
- America/Chicago
- America/Los_Angeles
- Europe/London
- Asia/Tokyo
- Asia/Kolkata
- Australia/Sydney

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/appointments/available-slots?date=2026-03-10&timezone=America/New_York" \
  -H "Accept: application/json"
```

#### Response Example (Success - 200)
```json
{
  "status": "success",
  "data": "Available slots for 2026-03-10:\n• 09:00 AM (2026-03-10T09:00:00Z)\n• 10:00 AM (2026-03-10T10:00:00Z)\n• 02:00 PM (2026-03-10T14:00:00Z)\n• 03:30 PM (2026-03-10T15:30:00Z)\n• 04:30 PM (2026-03-10T16:30:00Z)"
}
```

---

### 2. Book New Appointment
**Endpoint:** `POST /appointments/book`  
**Status:** ✅ Active  
**Authentication:** Not Required  
**Response Code:** 200 OK

#### Request Body
```json
{
  "datetime_natural": "tomorrow at 3pm",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-0123",
  "timezone": "America/New_York",
  "notes": "First time patient, has questions about services"
}
```

#### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| datetime_natural | string | Yes | Natural language date/time (e.g., "tomorrow at 3pm", "next Friday 2pm") |
| name | string | Yes | Patient/customer full name |
| email | string | Yes | Valid email address |
| phone | string | Yes | Phone number with country code |
| timezone | string | Yes | Patient's timezone |
| notes | string | No | Additional booking notes |

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/appointments/book" \
  -H "Content-Type: application/json" \
  -d '{
    "datetime_natural": "tomorrow at 3pm",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-0123",
    "timezone": "America/New_York",
    "notes": "First time patient"
  }'
```

#### Response Example (Success - 200)
```json
{
  "status": "success",
  "data": "Your appointment has been successfully booked! 🎉\n\n📋 Booking Details:\n• Name: John Doe\n• Date & Time: March 15, 2026 at 03:00 PM\n• Email: john.doe@example.com\n• Phone: +1-555-0123\n• Timezone: America/New_York\n• Booking ID: abc123xyz789\n\nA confirmation email will be sent to john.doe@example.com."
}
```

#### Response Example (Slot Unavailable - 200)
```json
{
  "status": "success",
  "data": {
    "status": "failed",
    "message": "This slot is no longer available",
    "suggested_slot": "2026-03-15T16:00:00Z"
  }
}
```

---

### 3. Get Booking Details
**Endpoint:** `GET /appointments/booking`  
**Status:** ✅ Active  
**Authentication:** Not Required  
**Response Code:** 200 OK

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | Patient email address |

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/appointments/booking?email=john.doe@example.com" \
  -H "Accept: application/json"
```

#### Response Example (Success - 200)
```json
{
  "status": "success",
  "data": "📋 Appointment Details:\n• Patient: John Doe\n• Email: john.doe@example.com\n• Phone: +1-555-0123\n• Date & Time: March 15, 2026 at 03:00 PM\n• Timezone: America/New_York\n• Status: ACCEPTED\n• Booking ID: abc123xyz789\n• Notes: First time patient"
}
```

#### Response Example (No Booking Found - 200)
```json
{
  "status": "success",
  "data": "No appointment found for this email address."
}
```

---

### 4. Reschedule Appointment
**Endpoint:** `POST /appointments/reschedule`  
**Status:** ✅ Active  
**Authentication:** Not Required  
**Response Code:** 200 OK

#### Request Body
```json
{
  "email": "john.doe@example.com",
  "new_start": "next Friday at 10am",
  "reason": "Conflict with other meeting",
  "timezone": "America/New_York"
}
```

#### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Patient email address |
| new_start | string | Yes | New appointment time (natural language) |
| reason | string | No | Reason for rescheduling |
| timezone | string | Yes | Patient's timezone |

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/appointments/reschedule" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "new_start": "next Friday at 10am",
    "reason": "Conflict with other meeting",
    "timezone": "America/New_York"
  }'
```

#### Response Example (Success - 200)
```json
{
  "status": "success",
  "data": "Your appointment has been successfully rescheduled! ✅\n\n📋 New Details:\n• New Date & Time: March 21, 2026 at 10:00 AM\n• Timezone: America/New_York\n• Booking ID: abc123xyz789\n\nA confirmation email will be sent to john.doe@example.com."
}
```

#### Response Example (Slot Unavailable - 200)
```json
{
  "status": "success",
  "data": "The requested time slot is not available. Please choose a different time."
}
```

#### Response Example (No Booking Found - 200)
```json
{
  "status": "success",
  "data": "No upcoming appointment found to reschedule."
}
```

---

### 5. Cancel Appointment
**Endpoint:** `POST /appointments/cancel`  
**Status:** ✅ Active  
**Authentication:** Not Required  
**Response Code:** 200 OK

#### Request Body
```json
{
  "email": "john.doe@example.com",
  "reason": "No longer need the appointment"
}
```

#### Request Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Patient email address |
| reason | string | No | Reason for cancellation |

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/appointments/cancel" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "reason": "No longer need the appointment"
  }'
```

#### Response Example (Success - 200)
```json
{
  "status": "success",
  "data": "Your appointment has been successfully cancelled. ✅\n\n• Booking ID: abc123xyz789\n• Status: Cancelled\n• Appointment was: March 15, 2026 at 03:00 PM\n\nWe're sorry to see you go! If you'd like to book again in the future, we're here to help."
}
```

#### Response Example (No Booking Found - 200)
```json
{
  "status": "success",
  "data": "No upcoming booking found to cancel."
}
```

---

## Error Handling

### Standard Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message explaining what went wrong"
}
```

### Common HTTP Status Codes

#### 400 - Bad Request
Invalid request parameters or malformed data.

```json
{
  "detail": "Invalid request parameters"
}
```

**Common causes:**
- Missing required fields
- Invalid data types
- Invalid UUID format
- Invalid date format

#### 401 - Unauthorized
Missing or invalid authentication token.

```json
{
  "detail": "Invalid or expired token"
}
```

**Common causes:**
- Missing Bearer token
- Expired access token (use refresh token to get new one)
- Invalid token format

#### 403 - Forbidden
Authenticated, but not authorized to access resource.

```json
{
  "detail": "Not authorized to access this agent"
}
```

**Common causes:**
- Trying to access another user's agent
- Insufficient permissions

#### 404 - Not Found
Requested resource not found.

```json
{
  "detail": "Agent not found"
}
```

**Common causes:**
- Invalid agent/action/KB ID
- Resource has been deleted
- Resource doesn't belong to authenticated user

#### 409 - Conflict
Request conflicts with existing data.

```json
{
  "detail": "Email already registered"
}
```

**Common causes:**
- Creating duplicate resource
- Trying to add tool already assigned to agent

#### 413 - Payload Too Large
File exceeds maximum size.

```json
{
  "detail": "File too large. Maximum size is 10MB"
}
```

#### 429 - Too Many Requests
Rate limit exceeded.

```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

#### 500 - Internal Server Error
Server encountered unexpected error.

```json
{
  "detail": "Internal server error"
}
```

#### 501 - Not Implemented
Endpoint is not yet implemented.

```json
{
  "detail": "Knowledge base upload not yet implemented"
}
```

---

## Helper Scripts

### Extract and Store Access Token

**Bash Script:**
```bash
#!/bin/bash

# Login and extract access token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }' | jq -r '.access_token')

# Save to file for use in other scripts
echo "export API_TOKEN=$TOKEN" > .auth_token.sh

echo "Access token saved to .auth_token.sh"
echo "Token: $TOKEN"
```

### Use Stored Token in Requests

**Bash Script:**
```bash
#!/bin/bash

# Load token from file
source .auth_token.sh

# Use in request
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Accept: application/json" | jq '.'
```

### Create Agent and Store ID

**Bash Script:**
```bash
#!/bin/bash

source .auth_token.sh

RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/agents" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Agent",
    "description": "Created via script"
  }')

AGENT_ID=$(echo $RESPONSE | jq -r '.id')

echo "Agent created: $AGENT_ID"
echo "export AGENT_ID=$AGENT_ID" >> .auth_token.sh
```

### Batch Update Multiple Agents

**Bash Script:**
```bash
#!/bin/bash

source .auth_token.sh

# Update all agents with new system prompt
AGENTS=$(curl -s -X GET "http://localhost:8000/api/v1/agents?limit=100" \
  -H "Authorization: Bearer $API_TOKEN" | jq -r '.items[].id')

for AGENT_ID in $AGENTS; do
  echo "Updating agent: $AGENT_ID"
  curl -X PUT "http://localhost:8000/api/v1/agents/$AGENT_ID" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "system_prompt": "You are a professional AI assistant..."
    }'
done
```

### Test All Agent Endpoints

**Bash Script:**
```bash
#!/bin/bash

set -e

source .auth_token.sh

echo "=== Testing Agent Endpoints ==="

# 1. Create agent
echo "1. Creating agent..."
AGENT=$(curl -s -X POST "http://localhost:8000/api/v1/agents" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Agent", "description": "Test"}')
AGENT_ID=$(echo $AGENT | jq -r '.id')
echo "Created: $AGENT_ID"

# 2. List agents
echo -e "\n2. Listing agents..."
curl -s -X GET "http://localhost:8000/api/v1/agents?limit=5" \
  -H "Authorization: Bearer $API_TOKEN" | jq '.items | length'

# 3. Search agents
echo -e "\n3. Searching agents..."
curl -s -X GET "http://localhost:8000/api/v1/agents/search?q=Test" \
  -H "Authorization: Bearer $API_TOKEN" | jq 'length'

# 4. Get agent details
echo -e "\n4. Getting agent details..."
curl -s -X GET "http://localhost:8000/api/v1/agents/$AGENT_ID" \
  -H "Authorization: Bearer $API_TOKEN" | jq '.name'

# 5. Update agent
echo -e "\n5. Updating agent..."
curl -s -X PUT "http://localhost:8000/api/v1/agents/$AGENT_ID" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Test Agent"}' | jq '.name'

# 6. Get available tools
echo -e "\n6. Getting available tools..."
curl -s -X GET "http://localhost:8000/api/v1/agents/tools/available" \
  -H "Authorization: Bearer $API_TOKEN" | jq 'length'

# 7. Delete agent
echo -e "\n7. Deleting agent..."
curl -s -X DELETE "http://localhost:8000/api/v1/agents/$AGENT_ID" \
  -H "Authorization: Bearer $API_TOKEN"
echo "Deleted: $AGENT_ID"

echo -e "\n=== All tests completed ==="
```

---

## Documentation Notes

**Last Updated:** March 7, 2026

### Important Information

1. **Authentication:**
   - Most endpoints require Bearer token in `Authorization` header
   - Format: `Authorization: Bearer YOUR_ACCESS_TOKEN`
   - Access token expires in 15 minutes
   - Use refresh token to get new access token

2. **Pagination:**
   - List endpoints return paginated results
   - Default limit: 20, maximum 100
   - Use `skip` and `limit` for pagination

3. **Timestamps:**
   - All timestamps are in ISO 8601 format with UTC timezone
   - Example: `2026-03-07T08:42:33.011Z`

4. **UUIDs:**
   - Agent and Action IDs are UUIDs (v4)
   - Example: `123e4567-e89b-12d3-a456-426614174000`

5. **Error Handling:**
   - Always check HTTP status code first
   - Read `detail` field for error message
   - Refer to Error Handling section for common errors

6. **Rate Limits:**
   - Register: 3 requests/minute per IP
   - Login: 5 requests/minute per IP
   - Refresh: 10 requests/minute per IP
   - Google Login: 20 requests/minute per IP
   - Other endpoints: Check specific endpoint documentation

7. **CORS:**
   - Cross-Origin requests are allowed
   - Required headers are included in examples

### Recently Implemented Features

✅ Knowledge base document upload  
✅ Assign knowledge bases to agents  
✅ Update knowledge base assignments (enable/disable)  
✅ Remove knowledge bases from agents  
✅ Delete/manage knowledge bases  
✅ List user's knowledge bases  
✅ Get agent's assigned knowledge bases  

### Planned Features (Not Yet Implemented)

- User management endpoints
- LiveKit integration endpoints
- Webhook endpoints
- Advanced knowledge base search
- Knowledge base versioning
- File download/retrieval endpoints

---

## Contact & Support

For issues or questions about the API, please contact the development team or check the GitHub repository for updates.
