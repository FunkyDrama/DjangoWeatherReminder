from dataclasses import asdict

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .services import WeatherAPIClient


class WeatherAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        city = request.query_params.get("city")
        if not city:
            return Response(
                {"detail": "City parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        client = WeatherAPIClient()
        weather_data = client.get_current(city)
        return Response(asdict(weather_data))
