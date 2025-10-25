#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask приложение для распознавания русской речи с помощью Vosk
Используется для оценки произношения в веб-приложении
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import logging
from vosk_processor import VoiceProcessor

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание Flask приложения
app = Flask(__name__)

# Настройка CORS для работы с GitHub Pages
CORS(app, origins=[
    "https://kariwari13.github.io",
    "http://localhost:*",
    "http://127.0.0.1:*"
])

# Инициализация Vosk процессора
try:
    voice_processor = VoiceProcessor()
    logger.info("✅ Vosk модель успешно загружена")
except Exception as e:
    logger.error(f"❌ Ошибка загрузки Vosk модели: {e}")
    voice_processor = None

@app.route('/', methods=['GET'])
def health_check():
    """
    Проверка работоспособности сервера
    """
    if voice_processor and voice_processor.model:
        return jsonify({
            "status": "ok",
            "message": "Vosk Speech Recognition API работает",
            "model": "vosk-model-small-ru-0.22"
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": "Vosk модель не загружена"
        }), 503

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Эндпоинт для транскрипции аудио

    Принимает:
    - audio: аудио файл (WebM, OGG, WAV)

    Возвращает:
    - transcription: распознанный текст
    """
    try:
        # Проверка наличия файла
        if 'audio' not in request.files:
            return jsonify({
                "error": "Аудио файл не найден"
            }), 400

        audio_file = request.files['audio']

        if audio_file.filename == '':
            return jsonify({
                "error": "Пустое имя файла"
            }), 400

        # Сохранение временного файла
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name

        try:
            # Распознавание речи
            if not voice_processor:
                raise Exception("Vosk процессор не инициализирован")

            transcription = voice_processor.recognize_audio(temp_path)

            logger.info(f"Распознано: {transcription}")

            return jsonify({
                "transcription": transcription,
                "success": True
            }), 200

        finally:
            # Удаление временного файла
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        logger.error(f"Ошибка транскрипции: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/evaluate', methods=['POST'])
def evaluate():
    """
    Эндпоинт для оценки произношения

    Принимает:
    - audio: аудио файл (WebM, OGG, WAV)
    - expected: ожидаемый текст

    Возвращает:
    - transcription: распознанный текст
    - expected: ожидаемый текст
    - accuracy: процент точности (0-100)
    - feedback: текстовая обратная связь
    """
    try:
        # Проверка наличия файла и текста
        if 'audio' not in request.files:
            return jsonify({
                "error": "Аудио файл не найден"
            }), 400

        if 'expected' not in request.form:
            return jsonify({
                "error": "Ожидаемый текст не указан"
            }), 400

        audio_file = request.files['audio']
        expected_text = request.form['expected']

        # Сохранение временного файла
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name

        try:
            # Распознавание речи
            if not voice_processor:
                raise Exception("Vosk процессор не инициализирован")

            transcription = voice_processor.recognize_audio(temp_path)

            # Оценка точности
            accuracy, feedback = voice_processor.evaluate_pronunciation(
                transcription,
                expected_text
            )

            logger.info(f"Ожидалось: {expected_text}, Распознано: {transcription}, Точность: {accuracy}%")

            return jsonify({
                "transcription": transcription,
                "expected": expected_text,
                "accuracy": accuracy,
                "feedback": feedback,
                "success": True
            }), 200

        finally:
            # Удаление временного файла
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        logger.error(f"Ошибка оценки: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """
    Проверка здоровья сервиса (для Render.com)
    """
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
