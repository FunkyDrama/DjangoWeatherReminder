from rest_framework import viewsets, permissions
from .models import NotificationLog
from .serializers import NotificationLogSerializer


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationLogSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):

        return NotificationLog.objects.filter(
            subscription__user=self.request.user
        ).select_related("subscription", "subscription__city")
