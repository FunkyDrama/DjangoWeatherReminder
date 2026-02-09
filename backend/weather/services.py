from dataclasses import dataclass
from datetime import datetime
from django.conf import settings
import requests


@dataclass
class WeatherData:
    """
    Represents weather data for a specific point in time.

    This class encapsulates information about the weather, including
    temperature, humidity, condition, and the time the data was recorded.
    It is designed to be used for storing and transferring weather-related
    information.

    :ivar temperature: The temperature recorded in degrees.
    :type temperature: float
    :ivar humidity: The percentage of humidity in the atmosphere.
    :type humidity: int
    :ivar condition: A description of current weather conditions (e.g., "Sunny", "Rainy").
    :type condition: str
    :ivar icon: The icon code representing the weather condition.
    :type icon: str
    :ivar description: A more detailed description of the weather condition.
    :type description: str
    :ivar wind_speed: The speed of the wind in meters per second.
    :type wind_speed: float
    :ivar feels_like: The perceived temperature considering humidity and wind.
    :type feels_like: float
    :ivar timestamp: The date and time the weather data was recorded.
    :type timestamp: datetime
    """

    city: str
    temperature: float
    humidity: int
    condition: str
    icon: str
    description: str
    wind_speed: float
    feels_like: float
    timestamp: datetime


class WeatherAPIClient:
    """
    Handles interactions with the OpenWeatherMap API.

    This class provides methods to interact with OpenWeatherMap API to fetch
    current weather data for a given city. It uses the API key from the application
    settings to authenticate requests. The primary purpose of this client is to
    fetch the current weather information and format the data into structured
    objects.

    :ivar BASE_URL: The base URL of the OpenWeatherMap API. It is used to construct
        the full endpoint for API requests.
    :type BASE_URL: str
    :ivar API_KEY: The API key required for authenticating requests with the
        OpenWeatherMap API.
    :type API_KEY: str
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5"
    GEO_URL = "https://api.openweathermap.org/geo/1.0"
    API_KEY = settings.WEATHER_API_KEY

    def geocode(self, query: str, limit: int = 5) -> list[dict]:
        params = {"q": query, "limit": limit, "appid": self.API_KEY}
        resp = requests.get(f"{self.GEO_URL}/direct", params=params)
        resp.raise_for_status()
        return [
            {
                "name": item["name"],
                "country": item.get("country", ""),
                "state": item.get("state", ""),
                "lat": item["lat"],
                "lon": item["lon"],
            }
            for item in resp.json()
        ]

    def get_current(
        self, city_name: str = "", lat: float = None, lon: float = None
    ) -> WeatherData:
        params = {"appid": self.API_KEY, "units": "metric"}
        if lat is not None and lon is not None:
            params["lat"] = lat
            params["lon"] = lon
        else:
            params["q"] = city_name
        resp = requests.get(f"{self.BASE_URL}/weather", params=params)
        resp.raise_for_status()
        data = resp.json()
        return WeatherData(
            city=data["name"],
            temperature=data["main"]["temp"],
            humidity=data["main"]["humidity"],
            icon=data["weather"][0]["icon"],
            condition=data["weather"][0]["main"],
            wind_speed=data["wind"]["speed"],
            feels_like=data["main"]["feels_like"],
            description=data["weather"][0]["description"],
            timestamp=datetime.fromtimestamp(data["dt"]),
        )
