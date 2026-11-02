# Конвертация экспорта Telegram в Obsidian: руководство по созданию личной базы знаний

## Введение

Привет! Свежая инфа - это вода, но когда ее становится много, то можно утонуть. В эпоху информационного перегрузки вопрос организации личных данных становится критически важным. Telegram давно перестал быть просто мессенджером — для многих это основной источник новостей, образовательного контента и рабочих коммуникаций. Однако встроенные средства поиска и организации информации в Telegram ограничены, а тот поток инфы со всех моих каналов, групп, чатиков я лично объять в силу отсутствия времени не в состоянии. А тут еще траблы с блоками. В общем жалко мне стало всех ваших трудов по написанию постов и жадность моя заиграла и я решился объединить все ваши знания в один гигантский мозг - Obsidian. Но сделать это не в ручную, 54 тысячи сообщений с 500+ каналов это не реальная задача, а автоматизировать этот процесс. Да и в добавок, чтобы общаться с этой базой знаний, подключить к ней чат LLM - локально (вдруг Интернет рубанут) и через веб API. Погнали! P. S. да в конце статьи маленький бонус для вайб-кодеров. Вы ведь слышали уже что-то про кодинг АИ-агентов? ;)

Впечатляет вселенная знаний? Меня тоже!

Obsidian представляет собой мощную платформу для создания личной базы знаний с поддержкой связных заметок, графа связей и расширенного поиска. В данной статье мы рассмотрим процесс создания конвертера, который переносит данные из Telegram в Obsidian с сохранением медиафайлов, форматирования и метаданных. А также с применением эмбендинговой нейронки автоматизированно выстроим связи между этими казалось бы разрозненными данными, получив на выходе оффлайн клон мозга 500+ человек и будем с ним общаться!

Ваши мозги у меня в ноутбуке ;)

## Постановка задачи

### Исходные данные

Telegram Desktop позволяет экспортировать историю чатов в формате JSON и HTML. Структура экспорта включает:

```text
DataExport_YYYY-MM-DD/
├── result.json              # Метаданные экспорта
├── chats/
│   ├── chat_001/
│   │   ├── messages.html
│   │   └── photos/
│   └── chat_002/
│       └── ...
├── profile_pictures/
└── export_results.html
```

### Целевая структура

Для эффективной работы в Obsidian требуется следующая организация:

```text
Telegram_Export/
├── Index.md
├── Contacts/
├── Saved Messages/
├── Personal Chats/
├── Groups/
├── Channels/
└── Other Chats/
```

## Архитектура решения

### Компоненты системы

1. **Парсер JSON** — извлечение метаданных чатов и сообщений
2. **Индексатор медиа** — построение карты доступных файлов
3. **Конвертер контента** — преобразование формата Telegram в Markdown
4. **Менеджер файлов** — копирование и организация медиа
5. **Генератор структуры** — создание папок и индексных файлов

### Схема потока данных

```text
Telegram Export JSON → Парсинг → Индексация медиа → Конвертация → Obsidian Vault
                                  ↓
                            Копирование файлов
```

## Реализация конвертера

### Базовая конфигурация

Создадим файл конфигурации через переменные окружения:

```python
import os
from pathlib import Path

JSON_FILE = os.getenv('TELEGRAM_JSON_FILE', 'result.json')
EXPORT_BASE = Path(os.getenv('TELEGRAM_EXPORT_BASE', '.'))
OUTPUT_DIR = Path(os.getenv('OBSIDIAN_OUTPUT_DIR', 'Telegram_Export'))
PATCH_FILE = Path(os.getenv('PATCH_FILE', 'patch.txt'))
GENERATE_PATCH_FILE = os.getenv('GENERATE_PATCH_FILE', 'true').lower() == 'true'
COPY_MEDIA = os.getenv('COPY_MEDIA', 'true').lower() == 'true'
GROUP_BY_DAY = os.getenv('GROUP_BY_DAY', 'true').lower() == 'true'
```

### Класс конвертера

```python
class TelegramToObsidian:
    def __init__(self):
        self.data = None
        self.stats = {
            'chats': 0,
            'messages': 0,
            'media_files': 0,
            'contacts': 0
        }
        self.media_cache = {}
        self.media_index = {}
```

### Генерация индекса медиафайлов

Проблема: пути к файлам в JSON могут не совпадать с реальной структурой на диске.

Решение: предварительная индексация всех файлов экспорта.

```python
def generate_patch_file(self) -> bool:
    if not GENERATE_PATCH_FILE:
        return False
    
    try:
        result = subprocess.run(
            ['ls', '-R', str(EXPORT_BASE)],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        
        with open(PATCH_FILE, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        self.index_media_from_patch()
        return True
    except Exception as e:
        print(f"Ошибка генерации patch.txt: {e}")
        return False

def index_media_from_patch(self):
    media_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.mp4', '.webm', '.pdf', '.zip', '.mp3'
    }
    current_dir = None
    
    with open(PATCH_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.endswith(':'):
                current_dir = line[:-1]
                continue
            if current_dir:
                if any(line.endswith(ext) for ext in media_extensions):
                    full_path = Path(current_dir) / line
                    file_name = line
                    
                    # Создаём несколько ключей для надёжного поиска
                    self.media_index[file_name] = full_path
                    
                    if 'chats/' in str(full_path):
                        rel_path = str(full_path).split('chats/', 1)[-1]
                        self.media_index[rel_path] = full_path
```

### Поиск медиафайлов

Многоуровневая стратегия поиска обеспечивает надёжное сопоставление:

```python
def find_media_file(self, file_path: str) -> Optional[Path]:
    if not file_path or "(File not included" in str(file_path):
        return None
    
    file_name = Path(file_path).name
    
    # Стратегия 1: Поиск по имени файла
    if file_name in self.media_index:
        source_file = self.media_index[file_name]
        if source_file.exists():
            return source_file
    
    # Стратегия 2: Поиск по полному пути
    if file_path in self.media_index:
        source_file = self.media_index[file_path]
        if source_file.exists():
            return source_file
    
    # Стратегия 3: Поиск по частичному совпадению
    for index_name, index_path in self.media_index.items():
        if index_path.exists() and index_path.name == file_name:
            return index_path
    
    # Стратегия 4: Прямой путь относительно EXPORT_BASE
    possible_paths = [
        EXPORT_BASE / file_path,
        EXPORT_BASE / file_path.replace('chats/', ''),
        EXPORT_BASE / 'chats' / file_path.replace('chats/', ''),
    ]
    for path in possible_paths:
        if path.exists():
            return path
    
    return None
```

### Копирование файлов

Важное решение: медиафайлы копируются в папку с заметкой, а не в центральное хранилище. Это обеспечивает корректное отображение в Obsidian.

```python
def copy_media_file(self, source_path: str, note_folder: Path = None) -> Optional[str]:
    if not COPY_MEDIA or not source_path:
        return None
    
    # Проверка кэша
    if source_path in self.media_cache:
        return self.media_cache[source_path]['obsidian']
    
    # Поиск файла
    source_file = self.find_media_file(source_path)
    if not source_file or not source_file.exists():
        print(f"Файл не найден: {source_path}")
        return None
    
    # Целевая директория — папка заметки
    target_dir = note_folder if note_folder else OUTPUT_DIR / "Attachments"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    target_file = target_dir / source_file.name
    
    # Обработка коллизий имён
    if target_file.exists():
        stem = target_file.stem
        suffix = target_file.suffix
        counter = 1
        while target_file.exists():
            target_file = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1
    
    # Копирование
    try:
        shutil.copy2(source_file, target_file)
        self.stats['media_files'] += 1
        
        result_path = source_file.name
        
        self.media_cache[source_path] = {
            'obsidian': result_path,
            'source': str(source_file)
        }
        return result_path
    except Exception as e:
        print(f"Ошибка копирования: {e}")
        return None
```

### Преобразование форматирования

Telegram использует собственный формат для текста с сущностями. Необходимо преобразовать его в Markdown.

```python
def parse_text_entities(self, text: Union[str, List], entities: Optional[List[Dict]] = None) -> str:
    if isinstance(text, str) and ('<' in text or '&' in text):
        return self.html_to_markdown(text)
    
    if entities is not None and isinstance(entities, list) and isinstance(text, str):
        return self._process_entities(text, entities)
    
    if isinstance(text, list):
        return self._process_text_list(text)
    
    return str(text) if text else ""

def _process_single_entity(self, text: str, entity_type: str, entity: Dict) -> str:
    handlers = {
        'bold': lambda t: f"**{t}**",
        'italic': lambda t: f"*{t}*",
        'code': lambda t: f"`{t}`",
        'pre': lambda t: f"```\n{t}\n```",
        'underline': lambda t: f"<u>{t}</u>",
        'strikethrough': lambda t: f"~~{t}~~",
    }
    
    if entity_type in handlers:
        return handlers[entity_type](text)
    elif entity_type in ['link', 'text_link']:
        href = entity.get('href', text)
        return f"[{text}]({href})"
    elif entity_type == 'mention':
        username = text[1:] if text.startswith('@') else text
        return f"[{text}](https://t.me/{username})"
    elif entity_type == 'spoiler':
        return f"\n> [!spoiler] {text}\n"
    
    return text
```

### Обработка медиа в сообщениях

В JSON Telegram фотографии хранятся в ключе `photo`. Необходимо проверять наличие ключей, а не полагаться на `media_type`.

```python
def format_message(self, msg: Dict, note_folder: Path = None) -> str:
    content = []
    
    # Время и отправитель
    date = msg.get('date', '')
    if date:
        time_part = date.split(' ')[-1] if ' ' in date else date
        content.append(f"⏰ **{time_part}**")
    
    sender = msg.get('from')
    if sender:
        content.append(f" — *{sender}*")
    content.append("\n\n")
    
    # Текст сообщения
    text = msg.get('text', '')
    entities = msg.get('text_entities')
    
    if text or entities:
        body = self.parse_text_entities(text, entities)
        if body and body.strip():
            content.append(f"{body.strip()}\n\n")
    
    # Медиафайлы — проверка наличия ключей
    file_path = None
    media_type = None
    
    if 'photo' in msg:
        file_path = msg.get('photo')
        media_type = 'photo'
    elif 'video' in msg:
        file_path = msg.get('video')
        media_type = 'video_file'
    elif 'voice' in msg:
        file_path = msg.get('voice')
        media_type = 'voice_message'
    elif 'audio' in msg:
        file_path = msg.get('audio')
        media_type = 'audio_file'
    elif 'sticker' in msg:
        file_path = msg.get('sticker')
        media_type = 'sticker'
    else:
        file_path = msg.get('file')
        media_type = msg.get('media_type')
    
    if file_path and "(File not included" not in str(file_path):
        copied_path = self.copy_media_file(file_path, note_folder)
        
        if copied_path:
            file_name = msg.get('file_name', Path(file_path).name)
            
            if media_type in ['photo', 'sticker', 'animation', 'video_message']:
                content.append(f"![{file_name}]({copied_path})\n\n")
            elif media_type == 'video_file':
                content.append(f"[{file_name}]({copied_path})\n\n")
            else:
                content.append(f"[{file_name}]({copied_path})\n\n")
    
    content.append("---\n\n")
    return ''.join(content)
```

### Группировка по дням

Каждая точка на графе - это отдельный пост

Для больших экспортов рекомендуется группировать сообщения по датам:

```python
def process_chat(self, chat: Dict, index: int, total: int):
    chat_id = chat.get('id', 0)
    chat_type = chat.get('type', 'unknown')
    chat_name = chat.get('name', f"Chat_{chat_id}")
    
    folder = self.create_chat_folder(chat_type, chat_id, chat_name)
    messages = chat.get('messages', [])
    
    if GROUP_BY_DAY:
        messages_by_date = {}
        for msg in messages:
            date_str = msg.get('date', '')
            day_key = date_str.split(' ')[0] if ' ' in date_str else date_str[:10]
            messages_by_date.setdefault(day_key, []).append(msg)
        
        for day_date, day_messages in messages_by_date.items():
            filename = f"{day_date.replace(':', '-')}.md"
            filepath = folder / filename
            
            content = self.build_frontmatter(chat_type, chat_name, chat_id, day_date, len(day_messages))
            content += f"# {day_date}\n"
            
            for msg in day_messages:
                content += self.format_message(msg, folder)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
```

### Frontmatter для метаданных

YAML frontmatter обеспечивает возможность расширенного поиска и фильтрации:

```python
def build_frontmatter(self, chat_type: str, chat_name: str, chat_id: int,
                      day_date: str, message_count: int) -> str:
    fm = "---\n"
    fm += f"chat_type: {chat_type}\n"
    fm += f"chat_name: {chat_name}\n"
    fm += f"chat_id: {chat_id}\n"
    fm += f"date: {day_date}\n"
    fm += f"message_count: {message_count}\n"
    fm += "tags: [telegram, daily-note]\n"
    fm += "---\n"
    return fm
```

## Интеграция с AI для поиска

### Настройка локальных моделей

Для расширенного поиска по базе знаний можно подключить локальные LLM через Ollama:

```bash
# Установка Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Модель для эмбеддингов
ollama pull nomic-embed-text

# Модель для чата
ollama pull llama3.2:1b
```

### Плагин Smart Connections

В Obsidian устанавливается плагин Smart Connections с конфигурацией:

```text
API Provider: Ollama
Base URL: http://localhost:11434
Embedding Model: nomic-embed-text
Chat Model: llama3.2:1b
Context Size: 4096
```

### Альтернативные провайдеры

Для пользователей в России рассмотрите GigaChat от Сбера:

```text
API Provider: Custom
Base URL: https://gigachat.devices.sberbank.ru/api/v1
Chat Model: GigaChat-Pro
```

Преимущества:

* Серверы в РФ
* Соответствие 152-ФЗ
* Отличная поддержка русского языка

## Оптимизация производительности

### Проблемы больших экспортов

При обработке 100000+ сообщений возникают следующие проблемы:

1. **Потребление памяти** — загрузка всего JSON в память
2. **Время индексации** — сканирование тысяч файлов
3. **Дубликаты медиа** — одинаковые файлы в разных чатах

### Решения

```python
# Потоковая обработка JSON
def load_data_streaming(self, json_file: Path):
    with open(json_file, 'r', encoding='utf-8') as f:
        for chunk in json.load(f):
            yield chunk

# Кэширование хэшей файлов
import hashlib

def get_file_hash(self, file_path: Path) -> str:
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

# Пропуск пустых чатов
if len(messages) == 0:
    print(f"Пропущено: {chat_name} (0 сообщений)")
    continue
```

## Обработка ошибок

### Типичные проблемы и решения

| Проблема | Причина | Решение |
| --- | --- | --- |
| Файлы не копируются | Неправильный путь в JSON | Многоуровневый поиск |
| Битые изображения | Файл не скачан при экспорте | Проверка размера и сигнатуры |
| Кодировка | Русские символы в путях | `encoding='utf-8'` |
| Пустые чаты | Вы не автор в канале | Пропуск чатов с 0 сообщений |

### Валидация файлов

```python
def _is_valid_image(self, file_path: Path) -> bool:
    if not file_path.exists():
        return False
    
    # Минимальный размер 10 KB
    if file_path.stat().st_size < 10240:
        return False
    
    # Проверка сигнатуры JPEG
    with open(file_path, 'rb') as f:
        header = f.read(3)
        if file_path.suffix.lower() in ['.jpg', '.jpeg']:
            return header[:2] == b'\xff\xd8'
    
    return True
```

## Заключение

Создание конвертера Telegram в Obsidian решает несколько важных задач:

1. **Долгосрочное хранение** — независимость от платформы Telegram
2. **Расширенный поиск** — полнотекстовый поиск по всем сообщениям
3. **Связность знаний** — возможность связывать сообщения с другими заметками
4. **AI-аналитика** — подключение локальных моделей для умного поиска

### Метрики проекта

| Параметр | Значение |
| --- | --- |
| Обработано чатов | 454 |
| Создано заметок | 15000+ |
| Скопировано медиа | 50000+ |
| Время обработки | 30-60 минут |

### Направления развития

1. Поддержка голосовых сообщений (транскрибация)
2. Инкрементальный экспорт (только новые сообщения)
3. Веб-интерфейс для настройки
4. Поддержка других мессенджеров

Исходный код проекта доступен в [репозитории](https://github.com/Inna949Festchuk/telegram_obsidian_sync/tree/main). Для вопросов и предложений используйте Issues на GitHub.

[БОНУС (Техническая спецификация для команды AI-агентов)](https://github.com/Inna949Festchuk/telegram_obsidian_sync/blob/main/CLOUD.md) для создания подобной системы с помощью кодинг АИ-агента Qwen3-Coder-Next* или его аналога.

*Qwen3-Coder-Next — это передовая специализированная модель искусственного интеллекта от команды Qwen (Alibaba), предназначенная для написания и редактирования программного кода. Она была представлена в феврале 2026 года как часть линейки Qwen3.