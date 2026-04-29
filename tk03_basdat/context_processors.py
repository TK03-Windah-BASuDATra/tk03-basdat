def role(request):
    r = request.GET.get('role')
    if r not in ('admin', 'organizer', 'customer'):
        r = None  # guest / belum pilih role
    return {'role': r}