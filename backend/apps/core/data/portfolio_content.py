"""
Данные портфолио для команды ``seed_portfolio``.

- ``ARTICLES`` — метаданные статей Хабра. Полный текст берётся из соседних
  ``.md``-файлов в каталоге ``data/articles/``. Поле ``habr_url`` — ссылка на
  оригинал: seed_portfolio скачивает og:image статьи и делает её обложкой.
- ``PROJECTS`` — репозитории GitHub (все не-форки) для раздела «Проекты».
  Поле ``cover_image`` — путь к картинке в репозитории; seed_portfolio
  скачивает её и сохраняет как превью проекта.

Поля ``*_en`` намеренно пустые: при отсутствии перевода фронтенд/AI
корректно фолбэкт на русский (см. ``Project.get_field`` / ``Post.get_field``).
"""

# --------------------------------------------------------------------------- #
# Статьи (Хабр)
# --------------------------------------------------------------------------- #
ARTICLES = [
    {
        "file": "01_web_gis.md",
        "slug": "web-gis-geodjango-postgis",
        "title_ru": (
            "Практика реализации Веб-ГИС приложений и сервисов на основе "
            "открытых ресурсов. Начало"
        ),
        "published_at": "2024-10-06",
        "tags": ["geodjango", "postgis", "web-gis", "django", "arrow"],
        "habr_url": "https://habr.com/ru/articles/848558/",
    },
    {
        "file": "02_satellite.md",
        "slug": "satellite-imagery-gdal-numpy-matplotlib",
        "title_ru": (
            "Получение, обработка, анализ и визуализация спутниковых снимков "
            "с помощью библиотек: GDAL, numpy и matplotlib"
        ),
        "published_at": "2024-10-27",
        "tags": ["gis", "gdal", "landsat", "numpy", "spectral-indexes"],
        "habr_url": "https://habr.com/ru/articles/853736/",
    },
    {
        "file": "03_telegram_obsidian.md",
        "slug": "telegram-export-to-obsidian",
        "title_ru": (
            "Конвертация экспорта Telegram в Obsidian: руководство по созданию "
            "личной базы знаний"
        ),
        "published_at": "2026-04-01",
        "tags": ["telegram", "obsidian", "python", "knowledge-base", "llm"],
        "habr_url": "https://habr.com/ru/articles/1017772/",
    },
    {
        "file": "04_geoai_fire.md",
        "slug": "geoai-agent-fire-monitor",
        "title_ru": (
            "Как сделать GeoAI-агента, который ищет пожары и отправляет к этим "
            "местам пожарные расчеты и дроны"
        ),
        "published_at": "2026-10-07",
        "tags": ["geoai", "llm", "agents", "fire-monitor", "mcp"],
        "habr_url": "https://habr.com/ru/articles/1091794/",
    },
]

# --------------------------------------------------------------------------- #
# Проекты (GitHub, все не-форки). order: 1 — первый в бенто-сетке.
# --------------------------------------------------------------------------- #
GITHUB_OWNER = "Inna949Festchuk"


def _repo(name, description, language, branch, featured=False, cover_image=''):
    return {
        "name": name,
        "github_url": f"https://github.com/{GITHUB_OWNER}/{name}",
        "branch": branch,
        "description": description,
        "technologies": [language] if language else [],
        "is_featured": featured,
        "cover_image": cover_image,
    }


PROJECTS = [
    # --- Флагманские ------------------------------------------------------- #
    _repo(
        "GeoAi-agent_fire_space",
        "Система мониторинга пожаров с веб-картой, управляемая GeoAI-agent "
        "с интерфейсами MCP и REST",
        "Python", "main", featured=True,
        cover_image="Interface.png",
    ),
    _repo(
        "flight-planning",
        "Сервис планирования применения БВС с ИИ-помощником",
        "Python", "main", featured=True,
    ),
    _repo(
        "telegram_obsidian_sync",
        "Конвертер экспорта Telegram в Obsidian: личная база знаний с "
        "локальным LLM-поиском (Ollama)",
        "Python", "main", featured=True,
        cover_image="blog.png",
    ),
    _repo(
        "festchuk",
        "Этот сайт: AI-Driven Cyberpunk Portfolio на Next.js + Django + pgvector",
        "TypeScript", "master", featured=True,
    ),
    # --- Прочие собственные ------------------------------------------------ #
    _repo(
        "Arrow_Carbon",
        "Проект по расчету углеродных единиц на основе спутниковых снимков",
        "Python", "master",
    ),
    _repo(
        "santinel",
        "Классификация космических снимков",
        "Jupyter Notebook", "main",
    ),
    _repo(
        "geospatial_mts_25",
        "Geospatial analysis and geomarketing для хакатона MTS True Tech 2025",
        "HTML", "main",
    ),
    _repo(
        "auto_upload",
        "Локальное веб-приложение для массового асинхронного скачивания "
        "файлов и папок из Яндекс.Диска",
        "Python", "master",
    ),
    _repo(
        "deepseek",
        "Особенности взаимодействия с различными нейросетями при помощи "
        "фреймворка Ollama",
        "Shell", "main",
    ),
    _repo(
        "open-webui-deploy",
        "MTS TRUE TECH 26 — конфигурация для передачи заказчику",
        "Shell", "main",
    ),
    _repo(
        "geodjango",
        "Хакатон ЛЦТ 2024. Arrow (Веб-ГИС на GeoDjango)",
        "JavaScript", "main",
    ),
    _repo(
        "codespaces-jupyter",
        "StartApp. Arrow (Jupyter в GitHub Codespaces)",
        "Jupyter Notebook", "main",
    ),
    _repo(
        "DigitalKawkaz",
        "Парсер сайта-справки RuStore (ЦП Кавказ 2024)",
        "Python", "main",
    ),
    _repo(
        "Digital_ost",
        "Хакатон «Цифровой прорыв ДФО 2024»",
        "Python", "main",
    ),
    _repo(
        "Yandex_Intern_Day",
        "Решения задач Яндекс практики",
        "Python", "main",
    ),
    _repo(
        "Task_Yandex",
        "Задачи для собеседования в Яндекс",
        "Python", "main",
    ),
    _repo(
        "YandexAcademy",
        "Хендбук Основы Python",
        "Python", "main",
    ),
    _repo(
        "Schema-Am",
        "Схема движения по азимутам",
        "Python", "master",
    ),
    _repo(
        "Project",
        "Программа для резервного копирования фото (аватарок) VK-профиля в облако",
        "Python", "master",
    ),
    _repo(
        "my_portfolio",
        "Первое портфолио (GitHub Pages)",
        None, "main",
    ),
    _repo(
        "FULLSTACK",
        "Домашние задания по курсу «Fullstack-разработчик на Python» и 2 хакатона",
        "JavaScript", "main",
    ),
    _repo(
        "Game_ldt_25",
        "Бэкенд для игры",
        "Python", "main",
    ),
    _repo(
        "SnifferCOM",
        "Sniffer COM",
        "Python", "main",
    ),
    _repo(
        "zona",
        "Zona",
        "Python", "main",
    ),
    _repo(
        "GeoApp",
        "GeoApp",
        "Python", "main",
    ),
    _repo(
        "NeuroStartUp",
        "NeuroStartUp",
        None, "main",
    ),
    _repo(
        "To_the_server",
        "Папка для деплоя проектов на reg.ru",
        "Python", "main",
    ),
    _repo(
        "mvt",
        "MVT",
        "HTML", "main",
    ),
    _repo(
        "Inna949Festchuk",
        "Config files for my GitHub profile",
        None, "main",
    ),
    _repo(
        "installVSCode",
        "installVSCode",
        None, "main",
    ),
    _repo(
        "issues",
        "issues",
        None, "main",
    ),
    _repo(
        "revert",
        "revert",
        None, "main",
    ),
    _repo(
        "ignore",
        "ignore",
        "HTML", "main",
    ),
    _repo(
        "colab",
        "colab",
        None, "main",
    ),
    _repo(
        "new",
        "new",
        None, "main",
    ),
]
