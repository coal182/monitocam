from django.http import JsonResponse
from django.db import connection


def health_check(request):
    db_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        db_ok = False

    status = "healthy" if db_ok else "degraded"
    return JsonResponse({"status": status, "service": "monitocam", "database": "ok" if db_ok else "error"})
