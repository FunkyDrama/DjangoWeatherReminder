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
                required=True,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={200: None},
    )
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
