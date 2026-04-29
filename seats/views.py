from django.shortcuts import render

# TODO Replace w real db logic later
def manajemen_kursi(request):
	# TODO Replace w real seat and status data joined w HAS_RELATIONSHIP
	seats = [
		{"id": "seat_001", "section": "WVIP", "row": "A", "number": 1, "venue": "Jakarta Convention Center", "status": "Terisi"},
		{"id": "seat_002", "section": "WVIP", "row": "A", "number": 2, "venue": "Jakarta Convention Center", "status": "Tersedia"},
		{"id": "seat_003", "section": "WVIP", "row": "A", "number": 3, "venue": "Jakarta Convention Center", "status": "Tersedia"},
		{"id": "seat_004", "section": "VIP", "row": "B", "number": 1, "venue": "Jakarta Convention Center", "status": "Terisi"},
		{"id": "seat_005", "section": "VIP", "row": "B", "number": 2, "venue": "Jakarta Convention Center", "status": "Terisi"},
		{"id": "seat_006", "section": "VIP", "row": "B", "number": 3, "venue": "Jakarta Convention Center", "status": "Tersedia"},
		{"id": "seat_007", "section": "Category 1", "row": "C", "number": 1, "venue": "Jakarta Convention Center", "status": "Tersedia"},
		{"id": "seat_008", "section": "Category 1", "row": "C", "number": 2, "venue": "Jakarta Convention Center", "status": "Tersedia"},
		{"id": "seat_009", "section": "Category 1", "row": "C", "number": 3, "venue": "Jakarta Convention Center", "status": "Tersedia"},
	]

	total = len(seats)
	tersedia = sum(1 for s in seats if s["status"] == "Tersedia")
	terisi = sum(1 for s in seats if s["status"] == "Terisi")

	context = {
		"page_title": "Manajemen Kursi",
		"seats": seats,
		"total_seats": total,
		"available_seats": tersedia,
		"occupied_seats": terisi,
		"venues": ["Semua Venue", "Jakarta Convention Center"],
	}
	return render(request, "manajemen_kursi.html", context)
