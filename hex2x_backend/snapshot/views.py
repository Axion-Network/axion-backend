from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import HexUser
from .serializers import HexAddressSerializer


class HexAddressViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HexUser.objects.all()
    serializer_class = HexAddressSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
