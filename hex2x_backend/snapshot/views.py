from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import LimitOffsetPagination

from .models import HexUser
from .serializers import HexAddressSerializer


class HexAddressViewSetPagination(LimitOffsetPagination):
    default_limit = 100
    max_limit = 1000


class HexAddressViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HexUser.objects.all()
    lookup_field = 'user_address'

    serializer_class = HexAddressSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = HexAddressViewSetPagination
