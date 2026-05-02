# def role(request):
#     r = request.GET.get('role')
#     return {'role': r if r in ('admin', 'organizer', 'customer') else 'guest'}


# buat nanti kalo udah implementasi pake sql dan udah nyimpen role di session
def role(request):
    r = request.session.get('role')
    if r not in ('admin', 'organizer', 'customer'):
        r = 'guest'
    return {'role': r}