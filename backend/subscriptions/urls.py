from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionViewSet, CityViewSet

router = DefaultRouter()
router.register("cities", CityViewSet, basename="city")
router.register("", SubscriptionViewSet, basename="subscription")

urlpatterns = [
    path("", include(router.urls)),
]
