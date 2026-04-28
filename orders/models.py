# orders/models.py
import uuid
from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Lunas'),
        ('Cancelled', 'Dibatalkan'),
    ]

    order_id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_date     = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    total_amount   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    customer       = models.ForeignKey(
                        'accounts.Customer',          # ← string, bukan import langsung
                        on_delete=models.CASCADE,
                        related_name='orders'
                     )

    class Meta:
        db_table = 'ORDER'
        ordering = ['-order_date']

    def __str__(self):
        return str(self.order_id)


class Ticket(models.Model):
    ticket_id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_code = models.CharField(max_length=100, unique=True)
    category    = models.ForeignKey(
                        'events.TicketCategory',       # ← string
                        on_delete=models.CASCADE,
                        related_name='tickets'
                  )
    order       = models.ForeignKey(
                        Order,                         # ← model di file yang sama, langsung saja
                        on_delete=models.CASCADE,
                        related_name='tickets'
                  )

    class Meta:
        db_table = 'TICKET'

    def __str__(self):
        return self.ticket_code


class HasRelationship(models.Model):
    seat   = models.ForeignKey(
                'events.Seat',                         # ← string
                on_delete=models.CASCADE
             )
    ticket = models.ForeignKey(
                Ticket,
                on_delete=models.CASCADE
             )

    class Meta:
        db_table = 'HAS_RELATIONSHIP'
        unique_together = ('seat', 'ticket')


class OrderPromotion(models.Model):
    order_promotion_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promotion          = models.ForeignKey(
                            'events.Promotion',        # ← string
                            on_delete=models.CASCADE
                         )
    order              = models.ForeignKey(
                            Order,
                            on_delete=models.CASCADE,
                            related_name='promotions'
                         )

    class Meta:
        db_table = 'ORDER_PROMOTION'