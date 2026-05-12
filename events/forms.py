from django import forms
from django.forms import formset_factory

class VenueForm(forms.Form):
    venue_name = forms.CharField(label="Nama Venue", max_length=100)
    capacity = forms.IntegerField(label="Kapasitas", min_value=1)
    city = forms.CharField(label="Kota", max_length=100)
    address = forms.CharField(label="Alamat", widget=forms.Textarea(attrs={"rows": 3}))
    seating_type = forms.ChoiceField(
        label="Tipe Seating",
        choices=[("reserved", "Reserved Seating"), ("free", "Free Seating")],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "seating_type":
                field.widget.attrs.update({"class": "form-select"})
            else:
                field.widget.attrs.update({"class": "form-control"})

class EventForm(forms.Form):
    event_title = forms.CharField(label="Judul Event", max_length=200)
    venue = forms.ChoiceField(label="Venue")
    event_datetime = forms.DateTimeField(
        label="Tanggal & Waktu Event",
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
    )
    image_url = forms.URLField(label="Image URL", required=False)
    description = forms.CharField(
        label="Deskripsi",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args, venues=None, **kwargs):
        super().__init__(*args, **kwargs)
        venues = venues or []
        self.fields["venue"].choices = [(v.venue_id, v.venue_name) for v in venues]
        for name, field in self.fields.items():
            if name == "venue":
                field.widget.attrs.update({"class": "form-select"})
            elif name not in ["event_datetime"]:
                field.widget.attrs.update({"class": "form-control"})

class TicketCategoryForm(forms.Form):
    category_name = forms.CharField(label="Nama Kategori", max_length=100)
    price = forms.IntegerField(label="Harga", min_value=0)
    quota = forms.IntegerField(label="Kuota", min_value=1)
    DELETE = forms.BooleanField(label="Hapus", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "DELETE":
                continue
            field.widget.attrs.update({"class": "form-control"})

TicketCategoryFormSet = formset_factory(
    TicketCategoryForm,
    extra=1,
    can_delete=True,
)

class EventArtistDummyForm(forms.Form):
    artist = forms.ChoiceField(label="Artis")
    role = forms.CharField(
        label="Role",
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Contoh: Headliner, Guest Star, Opening Act"
        })
    )
    DELETE = forms.BooleanField(label="Hapus", required=False)

    def __init__(self, *args, artist_choices=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["artist"].choices = artist_choices or []
        self.fields["artist"].widget.attrs.update({"class": "form-select"})

        for name, field in self.fields.items():
            if name != "DELETE":
                field.widget.attrs.setdefault("class", "form-control")


EventArtistFormSet = formset_factory(
    EventArtistDummyForm,
    extra=1,
    can_delete=True,
)
