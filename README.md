# Discord Music Bot

Това е Discord музикален бот, написан с `discord.py`, който използва slash команди и `yt-dlp` за търсене/пускане на музика. Ботът поддържа опашка от песни, пауза, продължаване, skip, връщане към предишна песен и управление на опашката.

## Функции

- `/play` — пуска песен или я добавя в опашката
- `/pause` — паузира текущата песен
- `/unpause` — продължава паузирана песен
- `/skip` — скипва текущата песен
- `/next` — същото като `/skip`
- `/previous` — връща предишната песен от историята
- `/queue show` — показва текущата песен и опашката
- `/queue remove` — премахва песен от опашката по номер
- `/queue add` — добавя песен на конкретна позиция в опашката

## Изисквания

Преди да стартираш бота, трябва да имаш:

- Python 3.10 или по-нова версия
- Discord bot token
- FFmpeg, инсталиран на компютъра/сървъра
- Инсталирани Python зависимости от `requirements.txt`

## Инсталация

1. Клонирай проекта или запази кода в папка:

```bash
git clone <your-repository-url>
cd <project-folder>
```

2. Създай виртуална среда:

```bash
python -m venv venv
```

3. Активирай виртуалната среда.

За Windows:

```bash
venv\Scripts\activate
```

За Linux/macOS:

```bash
source venv/bin/activate
```

4. Инсталирай зависимостите:

```bash
pip install -r requirements.txt
```

## Инсталиране на FFmpeg

Ботът използва FFmpeg, за да пуска аудио в Discord voice канал.

### Windows

1. Изтегли FFmpeg от официалния сайт.
2. Разархивирай го.
3. Добави папката `bin` към `PATH`.
4. Провери дали работи:

```bash
ffmpeg -version
```

### Linux / Ubuntu

```bash
sudo apt update
sudo apt install ffmpeg
```

### macOS

```bash
brew install ffmpeg
```

## Настройка на Discord бота

1. Отиди в Discord Developer Portal.
2. Създай ново приложение.
3. В секцията **Bot** създай бот.
4. Копирай token-а.
5. В кода намери този ред:

```python
TOKEN = ''
```

6. Постави token-а между кавичките:

```python
TOKEN = 'YOUR_BOT_TOKEN_HERE'
```

Важно: Не качвай token-а публично в GitHub.

## Покана на бота в сървър

Когато генерираш invite линк, избери следните scopes:

- `bot`
- `applications.commands`

Препоръчителни permissions:

- Connect
- Speak
- Use Voice Activity
- Send Messages
- Read Message History

## Стартиране

Стартирай бота с:

```bash
python bot.py
```

Ако файлът ти се казва различно, например `main.py`, използвай:

```bash
python main.py
```

При успешно стартиране в конзолата ще видиш съобщение, че slash командите са синхронизирани и ботът е онлайн.

## Команди

### `/play`

Пуска песен по име или линк.

Пример:

```text
/play query: never gonna give you up
```

Ако вече има песен, която свири, новата песен се добавя в опашката.

### `/pause`

Паузира текущата песен.

### `/unpause`

Продължава песента след пауза.

### `/skip`

Спира текущата песен и пуска следващата от опашката.

### `/next`

Алтернативна команда за `/skip`.

### `/previous`

Връща предишната песен от историята.

### `/queue show`

Показва текущата песен и всички песни в опашката.

### `/queue remove`

Премахва песен от опашката по номер.

Пример:

```text
/queue remove position: 2
```

### `/queue add`

Добавя песен на конкретна позиция в опашката.

Пример:

```text
/queue add position: 1 query: song name
```

## Важни бележки

- Ботът използва slash команди, затова може да отнеме малко време Discord да ги покаже в сървъра.
- FFmpeg трябва да бъде инсталиран и достъпен през терминала.
- `yt-dlp` може да има нужда от обновяване, ако YouTube промени начина си на работа:

```bash
pip install -U yt-dlp
```

- Не споделяй Discord token-а си публично.
- Ако ботът не влиза във voice канал, провери permissions на бота в Discord сървъра.

## Структура на проекта

Примерна структура:

```text
project-folder/
│
├── bot.py
├── requirements.txt
└── README.md
```

## Лиценз

Можеш да използваш и променяш проекта свободно.
