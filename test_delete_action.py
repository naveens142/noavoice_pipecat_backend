#!/usr/bin/env python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "admin@gmail.com"
PASSWORD = "Westack@12345"

# Login
r = requests.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Create agent
r = requests.post(f"{BASE_URL}/agents", json={"name": "Test"}, headers=headers)
agent_id = r.json()["id"]
print(f"Agent: {agent_id}")

# Get tools
r = requests.get(f"{BASE_URL}/agents/tools/available", headers=headers)
tools = r.json()
if tools:
    tool_id = tools[0]["id"]
    print(f"Tool: {tool_id}")
    
    # Add tool
    r = requests.post(f"{BASE_URL}/agents/{agent_id}/actions", 
        json={"tool_id": tool_id}, headers=headers)
    print(f"Add tool status: {r.status_code}")
    if r.status_code == 201:
        action_id = r.json()["id"]
        print(f"Action: {action_id}")
        
        # Try to delete
        r = requests.delete(f"{BASE_URL}/agents/{agent_id}/actions/{action_id}", headers=headers)
        print(f"Delete status: {r.status_code}")
        print(f"Response: {r.text}")
