from django.urls import path
from .views import WeatherAPIView, CityAutocompleteView


urlpatterns = [
    path("", WeatherAPIView.as_view(), name="weather"),
    path("cities/", CityAutocompleteView.as_view(), name="city-autocomplete"),
]
