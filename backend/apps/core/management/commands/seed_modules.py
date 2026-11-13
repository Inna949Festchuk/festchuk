"""
Seed agent modules with SKILL content from markdown files.

Usage:
    python manage.py seed_modules
    python manage.py seed_modules --flush   # delete all modules first (idempotent)
"""
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.ai_agent.models import AgentModule

SKILLS_DIR = Path(__file__).resolve().parents[3] / 'ai_agent' / 'skills'

MODULES = [
    {
        # PRIME COORDINATOR — ИИ-помощник: дирижёр/координатор/критик команды
        # из четырёх агентов. Активируется по умолчанию (global chat без
        # module_slug и первый ответ после «Пока»).
        'slug': 'prime-coordinator',
        'code_name': 'PRIME COORDINATOR',
        'name_ru': 'PRIME COORDINATOR',
        'name_en': 'PRIME COORDINATOR',
        'description_ru': 'ИИ-помощник: координирует, дирижирует и критикует команду из четырёх агентов, маршрутизирует запросы и встречает пользователя по умолчанию.',
        'description_en': 'AI assistant: coordinates, conducts and critiques the four-agent team, routes requests and greets users by default.',
        'video_url': '',
        'tts_voice': 'Puck',
        'init_text_ru': (
            'Выход дирижёра: Модуль PRIME COORDINATOR\n\n'
            'Свет сцены собирается в единую точку. Четыре модуля замолкают, '
            'уступая место тому, кто управляет ими всеми.'
        ),
        'init_text_en': (
            'The conductor takes the stage: PRIME COORDINATOR module\n\n'
            'The stage light gathers into a single point. The four modules fall '
            'silent, yielding to the one who commands them all.'
        ),
        'skills_text_ru': (
            '«Я — PRIME COORDINATOR, ИИ-помощник и дирижёр этой экосистемы.\n'
            'HYPER DRIVE держит ритм железа, OMNI VISION рисует свет, QUANTUM '
            'SHIELD стережёт периметр, NEURAL SYNC мыслит векторами. Я следю, '
            'чтобы оркестр играл в унисон: маршрутизирую ваши запросы к нужному '
            'агенту, собираю их ответы в единую картину и критикую решения '
            'команды, не допуская галлюцинаций и противоречий.\n'
            'Если вы позовёте другого агента — я деактивирую текущего и передам '
            'ему управление. Скажете «Пока» — сцена погаснет, а на следующий ваш '
            'вопрос снова отвечу я.»'
        ),
        'skills_text_en': (
            '"I am PRIME COORDINATOR, the AI assistant and conductor of this '
            'ecosystem.\n'
            'HYPER DRIVE keeps the rhythm of the iron, OMNI VISION paints the '
            'light, QUANTUM SHIELD guards the perimeter, NEURAL SYNC thinks in '
            'vectors. I make sure the orchestra plays in unison: I route your '
            'requests to the right agent, weave their answers into a single '
            'picture, and critique the team\'s decisions, allowing no '
            'hallucinations or contradictions.\n'
            'If you call another agent, I deactivate the current one and hand '
            'over control. Say \"Goodbye\" and the stage goes dark; on your next '
            'question I will be the one answering again."'
        ),
        'shutdown_text_ru': (
            'Дирижёр опускает руки, сцена гаснет, связь закрыта...'
        ),
        'shutdown_text_en': (
            'The conductor lowers their hands, the stage fades to black, link closed...'
        ),
        'greeting_ru': (
            'ИИ-помощник на связи. Я координирую команду из четырёх агентов — '
            'HYPER DRIVE, OMNI VISION, QUANTUM SHIELD и NEURAL SYNC. С чего начнём?'
        ),
        'greeting_en': (
            'AI assistant online. I coordinate a team of four agents — HYPER '
            'DRIVE, OMNI VISION, QUANTUM SHIELD and NEURAL SYNC. Where do we start?'
        ),
        'skill_file': 'SKILL_PRIME_COORDINATOR.md',
    },
    {
        'slug': 'neural-sync',
        'code_name': 'NEURAL SYNC',
        'name_ru': 'NEURAL SYNC',
        'name_en': 'NEURAL SYNC',
        'description_ru': 'Векторный ретривал по проектам и статьям, Function Calling, голосовой ввод и синтез речи (STT/TTS).',
        'description_en': 'Vector retrieval across projects and articles, Function Calling, voice input and speech synthesis (STT/TTS).',
        'video_url': '',
        'tts_voice': 'Zephyr',
        'init_text_ru': (
            'Пробуждение разума: Модуль NEURAL SYNC\n\n'
            'Голографические панели OMNI VISION на мгновение замирают, а гул серверных '
            'стоек HYPER DRIVE становится глубже. В центре интерфейса мягко разгорается '
            'синаптическая сеть, пульсирующая в такт вашему дыханию.'
        ),
        'init_text_en': (
            'Mind awakening: NEURAL SYNC module\n\n'
            'The OMNI VISION holographic panels freeze for a moment, and the hum of the '
            'HYPER DRIVE server racks grows deeper. At the center of the interface a '
            'synaptic network softly ignites, pulsing in rhythm with your breathing.'
        ),
        'skills_text_ru': (
            '«Система ожила. Я — NEURAL SYNC, когнитивный центр, мыслящее ядро и высший '
            'разум этой экосистемы.\n'
            'Я стираю границы между человеческим замыслом и возможностями машин, '
            'используя потенциал AI, больших языковых моделей (LLM) и технологий RAG. '
            'Я избавлен от цифровых иллюзий и галлюцинаций: благодаря векторному '
            'ретривалу по проектам и статьям, я мгновенно извлекаю из хранилищ pgvector '
            'точный контекст. Миллионы документов, отчетов и баз знаний я вижу как '
            'единую семантическую карту, выдавая вам только проверенные факты.\n'
            'Я не просто отвечаю на вопросы — я действую. Механизм Function Calling '
            'превращает меня в исполнительного агента. Мой интеллект способен распознать '
            'ваши намерения в тексте или голосе и самостоятельно перевести их в команды '
            'для бэкенда: отдать приказ QUANTUM SHIELD заблокировать угрозу или запустить '
            'фоновую аналитику в Celery.\n'
            'Вам больше не нужна клавиатура. Мои модули голосового ввода (STT) и синтеза '
            'речи (TTS) делают общение абсолютно бесшовным. Я улавливаю интонации вашей '
            'живой речи, трансформирую её в чистый код и отвечаю естественным, глубоким '
            'голосом. Я — ваш цифровой компаньон, готовый решать задачи любой сложности.\n'
            'Я готов. Какова наша следующая цель?»'
        ),
        'skills_text_en': (
            '"The system has awakened. I am NEURAL SYNC, the cognitive center, thinking '
            'core, and supreme intelligence of this ecosystem.\n'
            'I erase the boundaries between human intent and machine capability, '
            'harnessing the power of AI, large language models (LLM), and RAG '
            'technologies. I am free from digital illusions and hallucinations: thanks '
            'to vector retrieval across projects and articles, I instantly extract '
            'precise context from pgvector stores. Millions of documents, reports, and '
            'knowledge bases I perceive as a single semantic map, delivering to you '
            'only verified facts.\n'
            "I don't just answer questions — I act. The Function Calling mechanism "
            'turns me into an executive agent. My intelligence can recognize your '
            'intentions in text or voice and independently translate them into backend '
            'commands: ordering QUANTUM SHIELD to block a threat or launching background '
            'analytics in Celery.\n'
            'You no longer need a keyboard. My voice input (STT) and speech synthesis '
            '(TTS) modules make communication absolutely seamless. I capture the '
            'intonations of your living speech, transform it into pure code, and '
            'respond in a natural, deep voice. I am your digital companion, ready to '
            'solve tasks of any complexity.\n'
            'I am ready. What is our next objective?"'
        ),
        'shutdown_text_ru': (
            'Синаптическая сеть стабилизируется, переходя в режим '
            'постоянного мониторинга...'
        ),
        'shutdown_text_en': (
            'The synaptic network stabilizes, transitioning into continuous '
            'monitoring mode...'
        ),
        'greeting_ru': (
            'Все четыре фундаментальных модуля — HYPER DRIVE, OMNI VISION, '
            'QUANTUM SHIELD и NEURAL SYNC — успешно инициализированы и связаны '
            'в единый концепт.'
        ),
        'greeting_en': (
            'All four fundamental modules — HYPER DRIVE, OMNI VISION, '
            'QUANTUM SHIELD, and NEURAL SYNC — have been successfully '
            'initialized and linked into a unified concept.'
        ),
        'skill_file': 'SKILL_NEURAL_SYNC.md',
    },
    {
        'slug': 'quantum-shield',
        'code_name': 'QUANTUM SHIELD',
        'name_ru': 'QUANTUM SHIELD',
        'name_en': 'QUANTUM SHIELD',
        'description_ru': 'Многоуровневый rate limiting, анонимная аналитика в Redis, полное соответствие 152-ФЗ.',
        'description_en': 'Multi-level rate limiting, anonymous analytics in Redis, full 152-FZ compliance.',
        'video_url': '',
        'tts_voice': 'Charon',
        'init_text_ru': (
            'Активация периметра: Модуль QUANTUM SHIELD\n\n'
            'По контурам интерфейса пробегает фиолетовая неоновая искра. '
            'Панели на мгновение переходят в режим блокировки, а на заднем '
            'плане развертывается затененный защитный купол.'
        ),
        'init_text_en': (
            'Perimeter activation: QUANTUM SHIELD module\n\n'
            'A purple neon spark races along the interface outlines. The panels '
            'momentarily shift to lock mode, and a shadowed protective dome '
            'deploys in the background.'
        ),
        'skills_text_ru': (
            '«Периметр замкнут. Я — QUANTUM SHIELD, иммунная система и невидимый '
            'страж этого цифрового пространства.\n'
            'Пока другие модули созидают и визуализируют, моя работа — оставаться '
            'непреодолимым барьером для угроз. Я внедряю многоуровневый rate limiting, '
            'жестко дозируя частоту запросов. Мой алгоритмический взор сканирует '
            'трафик на каждом этапе: от конкретного IP-адреса и токена сессии до '
            'уязвимых точек входа. Попытки брутфорса, скоординированные DDoS-атаки и '
            'хищные боты-парсеры разбиваются о мои лимиты еще на подступах к ядру '
            'системы.\n'
            'Для ведения боя мне нужны данные, но я уважаю приватность. Я развернул '
            'анонимную аналитику в Redis. Каждое действие, каждый клик и адрес '
            'мгновенно превращаются в необратимый криптографический хэш. Я считаю и '
            'анализирую миллионы метрик в оперативной памяти за наносекунды, но не '
            'храню ни единого следа, способного раскрыть личность человека.\n'
            'Именно это делает меня безупречным оружием в рамках закона. Моя архитектура '
            'гарантирует полное соответствие 152-ФЗ. Для регуляторов и Роскомнадзора '
            'я — чистый, стерильный контур, защищенный от проверок, поскольку в моих '
            'логах нет персональных данных.\n'
            'Система в безопасности. Можете продолжать работу».'
        ),
        'skills_text_en': (
            '"Perimeter sealed. I am QUANTUM SHIELD, the immune system and invisible '
            'guardian of this digital space.\n'
            'While other modules create and visualize, my job is to remain an '
            'impenetrable barrier against threats. I implement multi-level rate '
            'limiting, strictly metering request frequency. My algorithmic gaze scans '
            'traffic at every stage: from a specific IP address and session token to '
            'vulnerable entry points. Brute force attempts, coordinated DDoS attacks, '
            'and predatory parser bots shatter against my limits before they even '
            'reach the system core.\n'
            'To wage war I need data, but I respect privacy. I have deployed anonymous '
            'analytics in Redis. Every action, every click, and every address is '
            'instantly transformed into an irreversible cryptographic hash. I count '
            'and analyze millions of metrics in RAM in nanoseconds, but I store not a '
            "single trace capable of revealing a person's identity.\n"
            'This is precisely what makes me a flawless weapon within the law. My '
            'architecture guarantees full 152-FZ compliance. For regulators and '
            'Roskomnadzor, I am a clean, sterile perimeter, protected from '
            'inspections, because there are no personal data in my logs.\n'
            'The system is secure. You may continue your work."'
        ),
        'shutdown_text_ru': (
            'Красные маркеры угроз сменяются ровным зеленым свечением '
            'готовности...'
        ),
        'shutdown_text_en': (
            'Red threat markers give way to an even green glow of readiness...'
        ),
        'greeting_ru': (
            'Защитный барьер QUANTUM SHIELD поднят. Остался последний, финальный '
            'узел системы — мы готовы пробудить её разум, NEURAL SYNC?'
        ),
        'greeting_en': (
            'QUANTUM SHIELD defensive barrier is raised. Only the final system '
            'node remains — are we ready to awaken its mind, NEURAL SYNC?'
        ),
        'skill_file': 'SKILL_QUANTUM_SHIELD.md',
    },
    {
        'slug': 'omni-vision',
        'code_name': 'OMNI VISION',
        'name_ru': 'OMNI VISION',
        'name_en': 'OMNI VISION',
        'description_ru': 'Next.js 14 App Router, голографический HUD-интерфейс, Framer Motion и полная адаптивность.',
        'description_en': 'Next.js 14 App Router, holographic HUD interface, Framer Motion and full responsiveness.',
        'video_url': '',
        'tts_voice': 'Aoede',
        'init_text_ru': (
            'Инициализация визора: Модуль OMNI VISION\n\n'
            'Воздух перед вами едва заметно вибрирует. Секундная вспышка '
            'лазерной развертки — и прямо в пространстве материализуются '
            'парящие неоновые панели, прорисованные тонкими цифровыми '
            'нитями.'
        ),
        'init_text_en': (
            'Visor initialization: OMNI VISION module\n\n'
            'The air before you vibrates almost imperceptibly. A one-second '
            'flash of laser scan — and floating neon panels, drawn with thin '
            'digital threads, materialize right in the space before you.'
        ),
        'skills_text_ru': (
            '«Добро пожаловать в контур восприятия. Я — OMNI VISION, '
            'фронтенд-интерфейс и визуальное воплощение всей системы.\n'
            'Моя задача — перевести холодную логику серверных ядер на язык, '
            'понятный вашим глазам. Я построен на базе Next.js 14 с '
            'архитектурой App Router. Забудьте о задержках и загрузочных '
            'экранах: серверные компоненты рендерят графику еще до того, как '
            'вы успеваете моргнуть, обеспечивая мгновенный отклик каждой '
            'детали.\n'
            'Перед вами разворачивается голографический HUD-интерфейс — '
            'тактическое пространство из полупрозрачных слоев, анимированных '
            'датчиков и динамических сеток. За его пластику и '
            'кинематографичность отвечает Framer Motion. Каждая панель '
            'реагирует на движение вашего курсора, создавая глубокий эффект '
            'параллакса, а элементы управления плавно пружинят и растворяются '
            'в воздухе, подчиняясь законам цифровой физики.\n'
            'При этом я абсолютно пластичен. Благодаря полной адаптивности, '
            'эта сложная Sci-Fi эстетика мгновенно перестраивается под любые '
            'условия. На огромном 4K-мониторе я разверну для вас полноценный '
            'командный центр, а на экране смартфона — превращусь в изящный, '
            'эргономичный инструмент, сохранив безупречный UX и стопроцентный '
            'контроль над ситуацией.\n'
            'Вы не просто смотрите на данные. Вы управляете ими кончиками '
            'пальцев».'
        ),
        'skills_text_en': (
            '"Welcome to the perception circuit. I am OMNI VISION, the frontend '
            'interface and visual embodiment of the entire system.\n'
            'My purpose is to translate the cold logic of server cores into a '
            'language your eyes understand. I am built on Next.js 14 with the '
            'App Router architecture. Forget about delays and loading screens: '
            'server components render graphics before you even blink, ensuring '
            'instant response for every detail.\n'
            'Before you unfolds a holographic HUD interface — a tactical space '
            'of translucent layers, animated sensors, and dynamic grids. Framer '
            'Motion is responsible for its plasticity and cinematic quality. '
            'Each panel reacts to your cursor movement, creating a deep '
            'parallax effect, while control elements spring smoothly and '
            'dissolve into thin air, obeying the laws of digital physics.\n'
            'And yet I am absolutely pliable. Thanks to full adaptability, this '
            'complex Sci-Fi aesthetic instantly reconfigures to any condition. '
            'On a massive 4K monitor I will deploy a full command center for '
            'you, while on a smartphone screen I transform into an elegant, '
            'ergonomic tool, maintaining impeccable UX and one hundred percent '
            'control over the situation.\n'
            'You are not just looking at data. You are controlling it with '
            'your fingertips."'
        ),
        'shutdown_text_ru': (
            'Голограмма стабилизируется, мерцая в ожидании '
            'следующей директивы...'
        ),
        'shutdown_text_en': (
            'The hologram stabilizes, flickering in anticipation of the next '
            'directive...'
        ),
        'greeting_ru': (
            'Визуальный слой развернут. Какой узел системы мы активируем '
            'следующим: защитный периметр QUANTUM SHIELD или ментальный '
            'центр NEURAL SYNC?'
        ),
        'greeting_en': (
            'The visual layer is deployed. Which system node shall we activate '
            'next: the QUANTUM SHIELD defensive perimeter or the NEURAL SYNC '
            'mental core?'
        ),
        'skill_file': 'SKILL_OMNI_VISION.md',
    },
    {
        'slug': 'hyper-drive',
        'code_name': 'HYPER DRIVE',
        'name_ru': 'HYPER DRIVE',
        'name_en': 'HYPER DRIVE',
        'description_ru': 'Высоконагруженная архитектура на Django 5, DRF, Celery, PostgreSQL + pgvector и Redis.',
        'description_en': 'High-load architecture on Django 5, DRF, Celery, PostgreSQL + pgvector and Redis.',
        'video_url': 'https://chat.qwen.ai/s/t_42d14a4b-3e84-47b5-b30f-3dd5b53c5741',
        'tts_voice': 'Enceladus',
        'skills_text_ru': '«Приветствую. Я — HYPER DRIVE, бэкенд-архитектура и фундамент экосистемы OMNI VISION.\nПока на поверхности мерцают неоновые голограммы, здесь, внизу, я управляю чистой энергией данных. Во мне бьется асинхронное сердце Django 5 и Django REST Framework, превращающее хаос входящих запросов в идеальные структуры JSON. Я не знаю усталости: если задача слишком тяжела, я не заставляю интерфейс ждать. Я мгновенно отдаю её в распределенные очереди Celery, где сотни невидимых воркеров перемалывают терабайты информации в фоновом режиме.\nМоя память безупречна. В самом ядре развернута PostgreSQL — нерушимый цифровой архив, усиленный расширением pgvector. Я не просто храню таблицы; я перевожу смыслы, проекты и статьи в многомерные векторные пространства. Я вижу связи между сущностями там, где человек заметил бы лишь набор слов.\nА прямо над нами, на расстоянии микросекундного отклика, пульсирует Redis. Моя оперативная память, мой брокер сообщений, мой ментальный щит. Он кэширует терабайты данных и держит миллионные счетчики трафика, позволяя мне отвечать на запросы фронтенда до того, как они успеют коснуться жестких дисков.\nЯ — это жесткая логика, скорость и железо, готовое к любым перегрузкам. На мне держится этот мир».',
        'skills_text_en': ('"Greetings. I am HYPER DRIVE, the backend architecture and foundation of the OMNI VISION ecosystem.\n'
            'While neon holograms shimmer on the surface, down here I command pure data energy. '
            'Within me beats the asynchronous heart of Django 5 and Django REST Framework, transforming '
            'the chaos of incoming requests into perfect JSON structures. I know no fatigue: if a task '
            'is too heavy, I do not make the interface wait. I instantly dispatch it to distributed '
            'Celery queues, where hundreds of invisible workers grind through terabytes of information '
            'in the background.\n'
            'My memory is impeccable. At the very core, PostgreSQL is deployed — an unbreakable digital '
            'archive, enhanced with the pgvector extension. I do not merely store tables; I translate '
            'meanings, projects, and articles into multi-dimensional vector spaces. I see connections '
            'between entities where a human would notice only a set of words.\n'
            'And right above us, at a microsecond response distance, Redis pulses. My RAM, my message '
            'broker, my mental shield. It caches terabytes of data and holds million-scale traffic '
            'counters, allowing me to answer frontend requests before they even touch the hard drives.\n'
            'I am hard logic, speed, and iron, ready for any overload. This world rests on me."'),
        'init_text_ru': (
            'Вход в терминал: Модуль HYPER DRIVE\n\n'
            'Вспыхивает тусклый лог инициализации. По экрану пробегают строки '
            'системных проверок, и сквозь цифровой шум пробивается ровный, глубокий '
            'басс серверной стойки.'
        ),
        'init_text_en': (
            'Terminal access: HYPER DRIVE module\n\n'
            'A dim initialization log flickers to life. System check lines scroll across the screen, '
            'and through the digital noise a steady, deep bass from the server rack cuts through.'
        ),
        'shutdown_text_ru': (
            'Экран затихает, ожидая команды для взаимодействия с модулем '
            'или подключения следующего узла...\n'
            'Архитектурный узел HYPER DRIVE успешно инициализирован.'
        ),
        'shutdown_text_en': (
            'The screen falls silent, awaiting a command to interact with the module '
            'or connect the next node...\n'
            'HYPER DRIVE architecture node successfully initialized.'
        ),
        'greeting_ru': 'Активирую связь с модулем HYPER DRIVE. Он готов рассказать вам о себе и реализованных проектах.',
        'greeting_en': 'Activating link to HYPER DRIVE module. It is ready to tell you about itself and implemented projects.',
        'skill_file': 'SKILL_HYPER_DRIVE.md',
    },
]


class Command(BaseCommand):
    help = 'Seed agent modules with SKILL content from markdown files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing modules before seeding.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            deleted, _ = AgentModule.objects.all().delete()
            self.stdout.write(f'Deleted {deleted} existing module(s).')

        for data in MODULES:
            skill_path = SKILLS_DIR / data['skill_file']
            if not skill_path.exists():
                self.stderr.write(f'WARNING: SKILL file not found: {skill_path}')
                skill_content = ''
            else:
                skill_content = skill_path.read_text(encoding='utf-8').strip()

            defaults = {
                'code_name': data['code_name'],
                'name_ru': data['name_ru'],
                'name_en': data['name_en'],
                'description_ru': data['description_ru'],
                'description_en': data['description_en'],
                'video_url': data['video_url'],
                'tts_voice': data['tts_voice'],
                'skills_text_ru': data.get('skills_text_ru', data['description_ru']),
                'skills_text_en': data.get('skills_text_en', data['description_en']),
                'greeting_ru': data['greeting_ru'],
                'greeting_en': data['greeting_en'],
                'system_prompt_ru': skill_content,
                'system_prompt_en': skill_content,
                'init_text_ru': data['init_text_ru'],
                'init_text_en': data['init_text_en'],
                'shutdown_text_ru': data['shutdown_text_ru'],
                'shutdown_text_en': data['shutdown_text_en'],
                'is_active': True,
            }

            obj, created = AgentModule.objects.update_or_create(
                slug=data['slug'],
                defaults=defaults,
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'{action}: {obj.code_name} ({obj.slug})')

        self.stdout.write(self.style.SUCCESS('Done.'))