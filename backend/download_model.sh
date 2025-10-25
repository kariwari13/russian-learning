#!/bin/bash
# Скрипт для скачивания Vosk модели для русского языка

set -e

echo "📥 Скачивание Vosk модели для русского языка..."

# URL модели
MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
MODEL_NAME="vosk-model-small-ru-0.22"

# Проверка наличия модели
if [ -d "$MODEL_NAME" ]; then
    echo "✅ Модель уже существует, пропускаем скачивание"
    exit 0
fi

# Скачивание модели
echo "📥 Загрузка модели (это может занять 1-2 минуты)..."
curl -L -o model.zip "$MODEL_URL"

# Распаковка
echo "📦 Распаковка модели..."
unzip -q model.zip

# Удаление архива
rm model.zip

echo "✅ Модель успешно установлена в $MODEL_NAME"
echo "📊 Размер модели:"
du -sh "$MODEL_NAME"
