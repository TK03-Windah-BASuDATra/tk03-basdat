def role(request):
    r = request.GET.get('role')
    if r not in ('admin', 'organizer', 'customer'):
        r = None  # guest (belum pilih role)
    return {'role': r}

# buat nanti kalo udah implementasi pake sql dan udah nyimpen role di session
# def role(request):
#     r = request.session.get('role')
#     if r not in ('admin', 'organizer', 'customer'):
#         r = None
#     return {'role': r}

