from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.exceptions import NotFound, APIException
from rest_framework.response import Response

from .models import HexUser, SnapshotUser, SnapshotUserTestnet
from .serializers import HexAddressSerializer


class HexAddressViewSetPagination(LimitOffsetPagination):
    default_limit = 100
    max_limit = 1000


class HexAddressViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SnapshotUserTestnet.objects.all()
    lookup_field = 'user_address'

    serializer_class = HexAddressSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = HexAddressViewSetPagination

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except:
            serializer = HexAddressSerializer()
            data = serializer.to_representation(kwargs)
            data_dict = dict(data)
            data_dict['hex_amount'] = 0
            return Response(data_dict)
