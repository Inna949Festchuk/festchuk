"""
Middleware, устраняющий петлю 301-редиректов между Next.js и Django.

Next.js (при `trailingSlash: true` + rewrite `/api/*`) при проксировании
отбрасывает завершающий слэш: Django получает `GET /api/projects` вместо
`GET /api/projects/`. Встроенный `CommonMiddleware` (APPEND_SLASH) отвечает на
это 301 → `/api/projects/`, запрос уходит обратно в Next.js, который снова
отбрасывает слэш → бесконечный цикл редиректов, и ни один `/api/*` (проекты,
статьи, чат, STT, TTS) не отдаёт данных.

Решение: для путей `/api/` завершающий слэш дописывается **на месте** (без
HTTP-редиректа) до URL-резолва, так что маршруты DRF (они всегда со слэшем)
матчатся с первого раза.
"""


class ApiTrailingSlashMiddleware:
    """Дописывает завершающий слэш к `/api/`-путям на месте (без 301)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if path.startswith("/api/") and not path.endswith("/"):
            fixed = path + "/"
            # path_info — то, что реально использует URL-резолвер.
            request.path_info = fixed
            request.META["PATH_INFO"] = fixed
            # path — для согласованности (logs, CommonMiddleware и т.д.).
            request.path = fixed
        return self.get_response(request)
