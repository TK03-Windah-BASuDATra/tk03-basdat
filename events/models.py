import uuid
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Venue(models.Model):
    SEATING_CHOICES = [
        ('reserved', 'Reserved Seating'),
        ('free', 'Free Seating'),
    ]

    venue_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue_name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    address = models.TextField()
    city = models.CharField(max_length=100)
    seating_type = models.CharField(max_length=20, choices=SEATING_CHOICES, default='free')

    class Meta:
        ordering = ['venue_name']

    def __str__(self):
        return self.venue_name

class Event(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_title = models.CharField(max_length=200)
    event_datetime = models.DateTimeField()
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='events')
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_events'
    )
    artists = models.TextField(blank=True, help_text='Pisahkan nama artis dengan koma')
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)

    class Meta:
        ordering = ['event_datetime']

    def __str__(self):
        return self.event_title

    @property
    def artist_list(self):
        return [a.strip() for a in self.artists.split(',') if a.strip()]

    @property
    def min_ticket_price(self):
        first_ticket = self.ticket_categories.order_by('price').first()
        return first_ticket.price if first_ticket else 0

class TicketCategory(models.Model):
    ticket_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_categories')
    category_name = models.CharField(max_length=100)
    price = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    quota = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f'{self.category_name} - {self.event.event_title}'