from rest_framework import serializers

from .models import SnapshotUser


class HexAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SnapshotUser
        exclude = ['id', 'snapshot_tx', 'tx_checked']
