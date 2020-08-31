from rest_framework import serializers

from .models import HexUser


class HexAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = HexUser
        exclude = ['id', 'blockchain_saved']
