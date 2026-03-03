#!/usr/bin/env python
"""Test the entire agent configuration system"""

import requests
import sys
import json
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"

# Default credentials
DEFAULT_EMAIL = "admin@gmail.com"
DEFAULT_PASSWORD = "Westack@12345"

# Test counters
tests_passed = 0
tests_failed = 0
access_token = None
headers = {
    "Content-Type": "application/json"
}


def login(email: str = DEFAULT_EMAIL, password: str = DEFAULT_PASSWORD) -> bool:
    """
    Login and get access token
    """
    global access_token, headers
    
    print(f"🔑 Logging in with {email}...")
    
    try:
        url = f"{BASE_URL}/auth/login"
        response = requests.post(
            url,
            json={
                "email": email,
                "password": password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            headers["Authorization"] = f"Bearer {access_token}"
            print(f"✅ Login successful\n")
            return True
        else:
            print(f"❌ Login failed (got {response.status_code})")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False


def test(name: str, method: str, endpoint: str, data: Optional[dict] = None, expected_status: int = 200) -> Optional[dict]:
    """
    Execute a test request and validate response
    """
    global tests_passed, tests_failed, access_token
    
    # Check if we have a valid token
    if not access_token:
        print(f"❌ {name} - No authentication token available")
        tests_failed += 1
        return None
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            r = requests.get(url, headers=headers)
        elif method == "POST":
            r = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            r = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            r = requests.delete(url, headers=headers)
        else:
            print(f"❌ {name} - Unknown HTTP method: {method}")
            tests_failed += 1
            return None
        
        if r.status_code == expected_status:
            print(f"✅ {name}")
            tests_passed += 1
            return r.json() if r.content else None
        else:
            print(f"❌ {name} (got {r.status_code}, expected {expected_status})")
            print(f"   Response: {r.text}")
            tests_failed += 1
            return None
    except Exception as e:
        print(f"❌ {name} - Error: {e}")
        tests_failed += 1
        return None


print("\n" + "="*70)
print("🚀 TESTING NOAVOICE AGENT CONFIGURATION SYSTEM")
print("="*70 + "\n")

# Step 1: Authentication
print("0️⃣ AUTHENTICATION")
print("-" * 70)
if not login():
    print("\n❌ Authentication failed. Exiting.")
    sys.exit(1)

# Test Group 1: Agent CRUD Operations
print("1️⃣ AGENT CRUD OPERATIONS")
print("-" * 70)

# Test 1.1: Create Agent
agent = test("Create agent", "POST", "/agents", {
    "name": "Test Agent",
    "description": "Integration test agent"
}, 201)

# Test 1.2: Create another agent for search/list tests
agent2 = test("Create second agent", "POST", "/agents", {
    "name": "Booking Assistant",
    "description": "Agent for handling bookings"
}, 201)

if agent:
    agent_id = agent.get('id')
    
    # Test 1.3: Get Agent Details
    test("Get agent details", "GET", f"/agents/{agent_id}")
    
    # Test 1.4: Update Agent Configuration
    test("Update agent (voice & prompt)", "PUT", f"/agents/{agent_id}", {
        "voice": "alloy",
        "system_prompt": "You are a helpful virtual assistant",
        "language": "EN",
        "timezone": "America/New_York"
    })
    
    # Test 1.5: Update Agent with more fields
    test("Update agent (messages)", "PUT", f"/agents/{agent_id}", {
        "first_message": "Hello! How can I help you?",
        "end_call_message": "Thank you for calling. Goodbye!",
        "voicemail_message": "Please leave a message after the beep."
    })
    
    # Test 1.6: List Agents with pagination
    test("List agents (default pagination)", "GET", "/agents")
    test("List agents (custom pagination)", "GET", "/agents?skip=0&limit=10")
    
    # Test 1.7: Search Agents
    test("Search agents by name", "GET", "/agents/search?q=Test")
    test("Search agents (booking)", "GET", "/agents/search?q=Booking")

# Test Group 2: Tools/Actions
print("\n2️⃣ TOOLS AND AGENT ACTIONS")
print("-" * 70)

# Test 2.1: Get Available Tools
tools_response = test("Get available tools", "GET", "/agents/tools/available")

if agent and tools_response:
    tools = tools_response
    
    if isinstance(tools, list) and len(tools) > 0:
        print(f"   Found {len(tools)} available tools")
        tool_id = tools[0].get('id')
        
        if tool_id:
            # Test 2.2: Add Tool to Agent
            action = test(
                "Add tool to agent", 
                "POST", 
                f"/agents/{agent_id}/actions",
                {
                    "tool_id": tool_id,
                    "custom_name": "Primary Tool"
                },
                201
            )
            
            if action:
                action_id = action.get('id')
                
                # Test 2.3: Update Action Configuration  
                if action_id:
                    test(
                        "Update action configuration",
                        "PUT",
                        f"/agents/{agent_id}/actions/{action_id}",
                        {
                            "custom_name": "Updated Tool Name",
                            "start_message": "Starting tool operation..."
                        }
                    )
                    
                    # Test 2.4: Remove Action
                    test(
                        "Remove action from agent",
                        "DELETE",
                        f"/agents/{agent_id}/actions/{action_id}",
                        None,
                        204
                    )
    else:
        print("   ⚠️  No available tools found")

# Test Group 3: Knowledge Base
print("\n3️⃣ KNOWLEDGE BASE MANAGEMENT")
print("-" * 70)

# Test 3.1: List Knowledge Bases
kb_response = test(
    "List knowledge bases",
    "GET",
    "/agents/knowledge-bases"
)

# Test 3.2: Create a dummy knowledge base file and upload
# Note: This requires a file, so we'll skip the actual upload in this test
print("   ℹ️  Knowledge base upload test skipped (requires file)")

# Test Group 4: Error Handling & Edge Cases
print("\n4️⃣ ERROR HANDLING & EDGE CASES")
print("-" * 70)

# Test 4.1: Create Agent without required field (should fail)
test(
    "Create agent without name (should fail)",
    "POST",
    "/agents",
    {"description": "No name provided"},
    422  # Unprocessable Entity
)

# Test 4.2: Get non-existent Agent (should fail)
test(
    "Get non-existent agent (should fail)",
    "GET",
    "/agents/00000000-0000-0000-0000-000000000000",
    None,
    404
)

# Test 4.3: Update non-existent Agent (should fail)
test(
    "Update non-existent agent (should fail)",
    "PUT",
    "/agents/00000000-0000-0000-0000-000000000000",
    {"voice": "test"},
    404
)

# Test 4.4: Invalid pagination
test(
    "List agents with invalid limit (should fail)",
    "GET",
    "/agents?limit=1000",  # Exceeds max of 100
    None,
    422
)

# Test Group 5: Cleanup
print("\n5️⃣ CLEANUP")
print("-" * 70)

if agent:
    agent_id = agent.get('id')
    test("Delete created agent", "DELETE", f"/agents/{agent_id}", None, 204)

if agent2:
    agent_id_2 = agent2.get('id')
    test("Delete second agent", "DELETE", f"/agents/{agent_id_2}", None, 204)

# Final Summary
print("\n" + "="*70)
print(f"📊 TEST RESULTS")
print("="*70)
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"📈 Total:  {tests_passed + tests_failed}")
print("="*70 + "\n")

sys.exit(0 if tests_failed == 0 else 1)