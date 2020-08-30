from django.db import models


class TokenTransfer(models.Model):
    from_address = models.CharField(max_length=100)
    to_address = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=len(str(2**256)), decimal_places=0, null=True, default=None)
    tx_hash = models.CharField(max_length=100, null=True, default=None)
    block_number = models.IntegerField(null=True, default=None)
