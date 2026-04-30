def role(request):
    r = request.GET.get('role', 'guest')
    if r not in ('guest', 'admin', 'organizer', 'customer'):
        r = 'guest'
    return {'role': r}