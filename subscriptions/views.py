from rest_framework import viewsets, permissions

from notifications.tasks import send_for_subscription
from .models import Subscription, City
from .serializers import SubscriptionSerializer, CitySerializer


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = (permissions.IsAuthenticated,)


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        sub = serializer.save(user=self.request.user)
        send_for_subscription(sub)
