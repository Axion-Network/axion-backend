from django.db import models


class TokenTransfer(models.Model):
    from_address = models.CharField(max_length=512)
    to_address = models.CharField(max_length=512)
    amount = models.DecimalField(max_digits=len(str(2**256)), decimal_places=0, null=True, default=None)
    tx_hash = models.CharField(max_length=512, null=True, default=None)
    block_number = models.IntegerField(null=True, default=None)


class TokenStakeStart(models.Model):
    address = models.CharField(max_length=512)
    stake_id = models.IntegerField()
    data0 = models.CharField(max_length=512)
    timestamp = models.IntegerField()
    hearts = models.DecimalField(max_digits=len(str(2**256)), decimal_places=0)
    shares = models.DecimalField(max_digits=len(str(2 ** 256)), decimal_places=0)
    days = models.IntegerField()
    is_autostake = models.BooleanField(default=False)
    tx_hash = models.CharField(max_length=512, null=True, default=None)
    block_number = models.IntegerField(null=True, default=None)


class TokenStakeEnd(models.Model):
    address = models.CharField(max_length=512)

    tx_hash = models.CharField(max_length=512, null=True, default=None)
    block_number = models.IntegerField(null=True, default=None)


class UserBalance(models.Model):
    address = models.CharField(max_length=512)
    balance_hex = models.DecimalField(max_digits=len(str(2**256)), decimal_places=0, null=True, default=None)
    balance_shares = models.DecimalField(max_digits=len(str(2**256)), decimal_places=0, null=True, default=None)
    token_transfers = models.ForeignKey(TokenTransfer, on_delete=models.SET_NULL, null=True, default=None)
    token_stakings_started = models.ForeignKey(TokenStakeStart, on_delete=models.SET_NULL, null=True, default=None)
    token_stakings_ended = models.ForeignKey(TokenStakeEnd, on_delete=models.SET_NULL, null=True, default=None)
