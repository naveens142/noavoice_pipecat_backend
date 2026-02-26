"""
Tool Schemas for LLM Function Calling
Defines JSON Schema for appointment management tools
"""

# ═══════════════════════════════════════════════════════════════════
# Tool Schemas for LLM Function Calling
# ═══════════════════════════════════════════════════════════════════


BOOKING_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_available_slots",
            "description": "Retrieve available appointment slots for a specific date. Use this to check availability before booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                        "description": "Date in YYYY-MM-DD format (e.g., 2026-02-26)"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Patient's timezone (e.g., 'Asia/Kolkata', 'America/New_York')",
                        "default": "Asia/Kolkata",
                        "enum": [
                            "Asia/Kolkata",
                            "America/New_York",
                            "America/Los_Angeles",
                            "Europe/London",
                            "Europe/Paris",
                            "Asia/Bangkok",
                            "Asia/Singapore",
                            "Australia/Sydney",
                            "UTC"
                        ]
                    }
                },
                "required": ["date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book a new dental appointment for a patient. Accept natural language date/time from user and pass directly to this function.",
            "parameters": {
                "type": "object",
                "properties": {
                    "datetime_natural": {
                        "type": "string",
                        "description": "Natural language date and time as stated by user. Examples: 'tomorrow at 3pm', 'next monday morning', 'august 25 at 2:30pm', 'friday afternoon'. Pass EXACTLY as user said it without conversion."
                    },
                    "name": {
                        "type": "string",
                        "description": "Patient's full name (first and last name)",
                        "minLength": 2,
                        "maxLength": 100
                    },
                    "email": {
                        "type": "string",
                        "format": "email",
                        "description": "Patient's valid email address for confirmation"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Patient's phone number with country code (e.g., +91-9876543210, +1-2025551234). Optional but recommended.",
                        "minLength": 10,
                        "maxLength": 20
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Patient's timezone for appointment scheduling",
                        "default": "Asia/Kolkata",
                        "enum": [
                            "Asia/Kolkata",
                            "America/New_York",
                            "America/Los_Angeles",
                            "Europe/London",
                            "Europe/Paris",
                            "Asia/Bangkok",
                            "Asia/Singapore",
                            "Australia/Sydney",
                            "UTC"
                        ]
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes or special requirements (e.g., 'First-time visit', 'Dental anxiety', 'Needs translation')",
                        "maxLength": 500
                    }
                },
                "required": ["datetime_natural", "name", "email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_booking",
            "description": "Retrieve existing booking details and appointment information by patient email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email",
                        "description": "Patient's registered email address to look up their booking"
                    }
                },
                "required": ["email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_appointment",
            "description": "Reschedule an existing appointment to a different date/time. Patient must have an active booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email",
                        "description": "Patient's registered email address"
                    },
                    "new_start": {
                        "type": "string",
                        "description": "New appointment date and time in natural language. Examples: 'tomorrow at 2pm', 'next week on wednesday', 'march 15 at 10:30am'. Pass EXACTLY as user said it."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for rescheduling (optional but helpful for bookkeeping)",
                        "maxLength": 300
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Patient's timezone",
                        "default": "Asia/Kolkata",
                        "enum": [
                            "Asia/Kolkata",
                            "America/New_York",
                            "America/Los_Angeles",
                            "Europe/London",
                            "Europe/Paris",
                            "Asia/Bangkok",
                            "Asia/Singapore",
                            "Australia/Sydney",
                            "UTC"
                        ]
                    }
                },
                "required": ["email", "new_start"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel an existing appointment. Patient must have an active booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email",
                        "description": "Patient's registered email address"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for cancellation (optional but useful for feedback)",
                        "maxLength": 300
                    }
                },
                "required": ["email"]
            }
        }
    },
]


WEATHER_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city"
                    },
                    "country": {
                        "type": "string",
                        "description": "Country code (optional, e.g., 'IN' for India)"
                    }
                },
                "required": ["city"]
            }
        }
    }
]


TOOL_SCHEMA_LISTS = [
    BOOKING_TOOLS_SCHEMA,
    WEATHER_TOOLS_SCHEMA,
    # Add more here as needed
]

# ALL_TOOLS_SCHEMA = [tool for schema_list in TOOL_SCHEMA_LISTS for tool in schema_list]