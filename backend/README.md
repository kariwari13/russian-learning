# 🎤 Russian Speech Recognition Backend (Vosk)

Backend API для распознавания русской речи и оценки произношения с использованием Vosk.

## 📋 Требования

- Python 3.10+
- FFmpeg (для конвертации аудио)
- ~50 MB свободного места (для Vosk модели)

## 🚀 Быстрый старт (локально)

### 1. Установка зависимостей

```bash
# Установка Python пакетов
pip install -r requirements.txt

# Установка FFmpeg (если еще не установлен)
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg

# Windows:
# Скачайте с https://ffmpeg.org/download.html
```

### 2. Скачивание Vosk модели

```bash
# Автоматическое скачивание
./download_model.sh

# Или вручную:
# 1. Скачайте https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
# 2. Распакуйте в папку backend/
```

### 3. Запуск сервера

```bash
# Для разработки (Flask dev server)
python app.py

# Для продакшена (Gunicorn)
gunicorn app:app --bind 0.0.0.0:5000
```

Сервер будет доступен на `http://localhost:5000`

## 🌐 Деплой на Render.com (БЕСПЛАТНО)

### Шаг 1: Подготовка

1. Создайте аккаунт на [Render.com](https://render.com)
2. Залогиньтесь через GitHub

### Шаг 2: Создание Web Service

1. Нажмите **"New +"** → **"Web Service"**
2. Подключите ваш GitHub репозиторий `russian-learning`
3. Настройте параметры:
   - **Name**: `russian-speech-recognition`
   - **Region**: `Frankfurt (EU Central)` (ближе к России)
   - **Branch**: `main` или ваша рабочая ветка
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```
     pip install -r requirements.txt && chmod +x download_model.sh && ./download_model.sh
     ```
   - **Start Command**:
     ```
     gunicorn app:app
     ```
   - **Instance Type**: **Free**

4. **Environment Variables** (необязательно):
   - `PYTHON_VERSION` = `3.11.0`

5. Нажмите **"Create Web Service"**

### Шаг 3: Ожидание деплоя

⏱️ Первый деплой займет 5-10 минут (скачивание модели).

После деплоя вы получите URL типа:
```
https://russian-speech-recognition.onrender.com
```

### Шаг 4: Проверка работы

Откройте в браузере:
```
https://russian-speech-recognition.onrender.com/
```

Должен вернуться JSON:
```json
{
  "status": "ok",
  "message": "Vosk Speech Recognition API работает",
  "model": "vosk-model-small-ru-0.22"
}
```

## 📡 API Эндпоинты

### 1. Health Check
```http
GET /
GET /health
```

**Ответ:**
```json
{
  "status": "ok",
  "message": "Vosk Speech Recognition API работает",
  "model": "vosk-model-small-ru-0.22"
}
```

### 2. Транскрипция
```http
POST /transcribe
Content-Type: multipart/form-data
```

**Параметры:**
- `audio` (file) - аудио файл (WebM, OGG, WAV)

**Пример (curl):**
```bash
curl -X POST \
  https://russian-speech-recognition.onrender.com/transcribe \
  -F "audio=@recording.webm"
```

**Ответ:**
```json
{
  "transcription": "мама",
  "success": true
}
```

### 3. Оценка произношения
```http
POST /evaluate
Content-Type: multipart/form-data
```

**Параметры:**
- `audio` (file) - аудио файл
- `expected` (string) - ожидаемый текст

**Пример (curl):**
```bash
curl -X POST \
  https://russian-speech-recognition.onrender.com/evaluate \
  -F "audio=@recording.webm" \
  -F "expected=МАМА"
```

**Ответ:**
```json
{
  "transcription": "мама",
  "expected": "мама",
  "accuracy": 100,
  "feedback": "Отлично! Идеальное произношение! 🌟",
  "success": true
}
```

### Коды ошибок

- **400**: Неверный запрос (нет файла или текста)
- **500**: Ошибка сервера (проблемы с Vosk)
- **503**: Сервис недоступен (модель не загружена)

## 🔧 Локальное тестирование

### Тест 1: Проверка работы API
```bash
# Проверка health check
curl http://localhost:5000/

# Должен вернуть:
# {"status": "ok", ...}
```

### Тест 2: Запись и тестирование аудио

1. Запишите короткое аудио (скажите "мама")
2. Сохраните как `test.webm` или `test.wav`
3. Отправьте на сервер:

```bash
curl -X POST \
  http://localhost:5000/evaluate \
  -F "audio=@test.webm" \
  -F "expected=мама"
```

## 📊 Ограничения бесплатного тира Render.com

- ✅ **750 часов** в месяц (достаточно для учебного проекта)
- ⏸️ Сервис **"засыпает"** после 15 минут неактивности
- ⏱️ **"Пробуждение"** занимает ~30 секунд при первом запросе
- 💾 **512 MB RAM** (достаточно для small модели Vosk)
- 🚫 **Нет персистентного хранилища** (модель загружается при каждом деплое)

**Решение проблемы "засыпания":**
- Используйте сервис [UptimeRobot](https://uptimerobot.com) для пинга каждые 5 минут
- Или добавьте "прогрев" при открытии вашего frontend

## 🐛 Troubleshooting

### Проблема: "Vosk модель не загружена"

**Решение:**
1. Проверьте логи деплоя на Render.com
2. Убедитесь что `download_model.sh` выполнился успешно
3. Проверьте что в Build Command указан скрипт скачивания

### Проблема: "FFmpeg not found"

**Решение:**
Render.com по умолчанию включает FFmpeg. Если ошибка повторяется:
1. Добавьте в `requirements.txt`:
   ```
   ffmpeg-python==0.2.0
   ```

### Проблема: 503 Service Unavailable

**Решение:**
- Сервис "заснул" - подождите 30 секунд и повторите запрос
- Или настройте UptimeRobot для поддержания сервиса активным

### Проблема: Медленное распознавание

**Решение:**
- Vosk small модель оптимизирована для скорости
- Убедитесь что аудио не длиннее 10 секунд
- Используйте сжатое аудио (WebM с низким битрейтом)

## 📝 Структура файлов

```
backend/
├── app.py                      # Flask приложение
├── vosk_processor.py           # Логика распознавания речи
├── requirements.txt            # Python зависимости
├── download_model.sh           # Скрипт скачивания модели
├── render.yaml                 # Конфигурация Render.com
├── .gitignore                  # Исключения для git
├── README.md                   # Эта документация
└── vosk-model-small-ru-0.22/   # Vosk модель (скачивается отдельно)
```

## 🔐 Безопасность

- ✅ CORS настроен только для вашего домена GitHub Pages
- ✅ Временные файлы автоматически удаляются
- ✅ Нет сохранения аудио на сервере
- ⚠️ Рекомендуется добавить rate limiting для продакшена

## 📚 Дополнительные ресурсы

- [Vosk Documentation](https://alphacephei.com/vosk/)
- [Vosk Models](https://alphacephei.com/vosk/models)
- [Render.com Docs](https://render.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

## 🆘 Поддержка

Если возникли проблемы:
1. Проверьте логи на Render.com: Dashboard → Your Service → Logs
2. Проверьте Issues в GitHub репозитории
3. Убедитесь что модель загрузилась (размер ~45 MB)

## ✅ Чеклист деплоя

- [ ] Аккаунт на Render.com создан
- [ ] Репозиторий подключен к Render
- [ ] Build Command указан правильно
- [ ] Start Command указан правильно
- [ ] Деплой прошел успешно (проверьте логи)
- [ ] Health check возвращает `{"status": "ok"}`
- [ ] Сохранили URL вашего backend
- [ ] Обновили frontend с URL backend
- [ ] Протестировали /evaluate эндпоинт

Удачи! 🚀
