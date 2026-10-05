from mcp.server.fastmcp import FastMCP
import requests
import os
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Weather MCP Server", port=8001)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

@mcp.tool()
def get_current_weather(city:str):
    """
    Get the current weather for a given city using the OpenWeatherMap API.
    """
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY is missing. Please add it to your .env file.")

   
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }
    )

    if response.status_code != 200:
        raise ValueError(f"Error fetching weather data: {response.text}")

    data = response.json()

    weather_info = {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "feels_like_c": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "condition": data["weather"][0]["description"],
        "wind_speed": data["wind"]["speed"],
        "description": data["weather"][0]["description"],
    }

    return weather_info

@mcp.tool()
def get_weather_forecast(city:str, days:int=3): #def get_weather_forecast(city:str, days:int=3):
    """
    Get the weather forecast for a given city for the next 'days' days using the OpenWeatherMap API.
    """

    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY is missing. Please add it to your .env file.")

    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
    )

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }


    response = requests.get(
        url,
        params=params
    )

    if response.status_code != 200:
        raise ValueError(f"Error fetching weather forecast data: {response.text}")

    data = response.json()

    forecast_info = []

    for day in data["list"][:5]:  # Get forecast for the next 5 days
        forecast_info.append(
        #     {
        #        "date": day["dt"],
        #        "temperature": day["temp"]["day"],
        #        "feels_like_c": day["feels_like"]["day"],
        #        "humidity": day["humidity"],
        #        "condition": day["weather"][0]["description"],
        #        "wind_speed": day["speed"],
        #        "description": day["weather"][0]["description"],
        #    }
            {
                "datetime": day["dt_txt"],
                "temperature": day["main"]["temp"],
                "weather": day["weather"][0]["description"]
            }
        )

    return  {
        "city" : city,
        "forecast" : forecast_info
    }

# Run this custom mcp inside your local machine
if __name__=="__main__":
    mcp.run()