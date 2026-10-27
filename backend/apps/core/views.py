"""
Core app views.
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache


def health_check(request):
    """Health check endpoint."""
    checks = {
        'status': 'ok',
        'database': 'unknown',
        'cache': 'unknown',
    }

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        checks['database'] = 'ok'
    except Exception:
        checks['database'] = 'error'
        checks['status'] = 'degraded'

    # Check cache
    try:
        cache.set('health_check', 'test', 10)
        if cache.get('health_check') == 'test':
            checks['cache'] = 'ok'
            cache.delete('health_check')
        else:
            checks['cache'] = 'error'
            checks['status'] = 'degraded'
    except Exception:
        checks['cache'] = 'error'
        checks['status'] = 'degraded'

    status_code = 200 if checks['status'] == 'ok' else 503
    return JsonResponse(checks, status=status_code)
