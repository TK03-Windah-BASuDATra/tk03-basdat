from django import forms
from django.forms import inlineformset_factory
from .models import Venue, Event, TicketCategory


class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ['venue_name', 'capacity', 'city', 'address', 'seating_type']
        widgets = {
            'venue_name': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'seating_type': forms.Select(attrs={'class': 'form-select'}),
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['event_title', 'event_datetime', 'venue', 'artists', 'description', 'image_url']
        widgets = {
            'event_title': forms.TextInput(attrs={'class': 'form-control'}),
            'event_datetime': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'venue': forms.Select(attrs={'class': 'form-select'}),
            'artists': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event_datetime'].input_formats = ['%Y-%m-%dT%H:%M']


class TicketCategoryForm(forms.ModelForm):
    class Meta:
        model = TicketCategory
        fields = ['category_name', 'price', 'quota']
        widgets = {
            'category_name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'quota': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

TicketCategoryFormSet = inlineformset_factory(
    Event,
    TicketCategory,
    form=TicketCategoryForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)