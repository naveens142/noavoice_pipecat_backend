"""
External Tools - Third-party integrations
Weather and other external API tools for LLM function calling
"""

import httpx
from app.config.logging import app_logger
import os
from dotenv import load_dotenv

load_dotenv()
logger = app_logger


async def get_weather(city: str, country: str = None) -> str:
    """
    Fetch current weather for a city using OpenWeatherMap API.
    
    Args:
        city (str): Name of the city (e.g., 'New Delhi', 'London')
        country (str, optional): ISO 3166 country code (e.g., 'IN', 'UK')
        
    Returns:
        str: Formatted weather information or error message
        
    Example:
        result = await get_weather("New Delhi", "IN")
        # Returns: "The weather in New Delhi is clear sky with a temperature of 28°C"
    """
    try:
        # ✅ STEP 1: Validate input
        # ═══════════════════════════════════════════════════════════════
        
        if not city or not isinstance(city, str):
            logger.warning("❌ Invalid city name provided")
            return "Please provide a valid city name."
        
        city = city.strip()
        
        # ✅ STEP 2: Get API configuration
        # ═══════════════════════════════════════════════════════════════
        
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not  api_key:
            logger.warning("⚠️ OpenWeatherMap API key not configured")
            return "Weather service is not configured. Please set OPENWEATHER_API_KEY."
        
        # ✅ STEP 3: Build request
        # ═══════════════════════════════════════════════════════════════
        
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        
        # Format city query
        if country:
            country = country.strip().upper()
            query = f"{city},{country}"
        else:
            query = city
        
        params = {
            "q": query,
            "appid": api_key,
            "units": "metric"
        }
        
        logger.info(f"🌡️ Fetching weather for: {query}")
        
        # ✅ STEP 4: Make API call
        # ═══════════════════════════════════════════════════════════════
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(base_url, params=params)
        
        # ✅ STEP 5: Handle response
        # ═══════════════════════════════════════════════════════════════
        
        if response.status_code == 404:
            logger.warning(f"❌ City not found: {query}")
            return f"City '{city}' not found. Please check the spelling and try again."
        
        if response.status_code == 401:
            logger.error("❌ Invalid OpenWeatherMap API key")
            return "Weather service authentication failed. Please contact support."
        
        if response.status_code != 200:
            logger.error(f"❌ Weather API error: {response.status_code} - {response.text}")
            return f"Could not fetch weather for {city}. Status code: {response.status_code}"
        
        # ✅ STEP 6: Parse response
        # ═══════════════════════════════════════════════════════════════
        
        data = response.json()
        
        # Extract weather information
        weather_info = data.get("weather", [])
        main_info = data.get("main", {})
        wind_info = data.get("wind", {})
        
        if not weather_info or not main_info:
            logger.error("❌ Invalid API response format")
            return "Could not parse weather data. Please try again."
        
        description = weather_info[0].get("description", "Unknown").title()
        temperature = main_info.get("temp", "N/A")
        feels_like = main_info.get("feels_like", "N/A")
        humidity = main_info.get("humidity", "N/A")
        wind_speed = wind_info.get("speed", "N/A")
        
        # ✅ STEP 7: Format response
        # ═══════════════════════════════════════════════════════════════
        
        location = f"{city}, {country}" if country else city
        
        response_text = (
            f"🌡️ Weather in {location}:\n"
            f"• Condition: {description}\n"
            f"• Temperature: {temperature}°C\n"
            f"• Feels like: {feels_like}°C\n"
            f"• Humidity: {humidity}%\n"
            f"• Wind Speed: {wind_speed} m/s"
        )
        
        logger.info(f"✅ Weather fetched successfully for {location}")
        return response_text
        
    except httpx.TimeoutException:
        logger.error(f"⏱️ Weather API timeout for {city}")
        return "Weather service is taking too long. Please try again."
        
    except httpx.RequestError as e:
        logger.error(f"❌ Network error fetching weather: {str(e)}", exc_info=True)
        return f"Could not connect to weather service. Please check your internet connection."
        
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_weather: {str(e)}", exc_info=True)
        return f"An error occurred while fetching weather. Please try again later."
