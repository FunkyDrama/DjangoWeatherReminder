from rest_framework import viewsets, permissions
from rest_framework.pagination import LimitOffsetPagination

from .models import NotificationLog
from .serializers import NotificationLogSerializer


class LogsPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationLogSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LogsPagination

    def get_queryset(self):
        return (
            NotificationLog.objects.filter(subscription__user=self.request.user)
            .select_related("subscription", "subscription__city")
            .order_by("-sent_at", "-id")
        )
