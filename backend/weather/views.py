from dataclasses import asdict

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from .services import WeatherAPIClient


class WeatherAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="city",
                description="City name for current weather",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="lat",
                description="Latitude",
                required=False,
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="lon",
                description="Longitude",
                required=False,
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={200: None},
    )
    def get(self, request):
        city = request.query_params.get("city")
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not city and (lat is None or lon is None):
            return Response(
                {"detail": "Provide 'city' or both 'lat' and 'lon'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = WeatherAPIClient()
        if lat is not None and lon is not None:
            weather_data = client.get_current(lat=float(lat), lon=float(lon))
        else:
            weather_data = client.get_current(city_name=city)
        return Response(asdict(weather_data))


class CityAutocompleteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="q",
                description="City name query for autocomplete",
                required=True,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={200: None},
    )
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response([])
        client = WeatherAPIClient()
        try:
            results = client.geocode(query)
        except Exception:
            return Response([], status=status.HTTP_200_OK)
        return Response(results)
