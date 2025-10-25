#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обработка речи через Vosk для оценки произношения
"""

import os
import json
import wave
import subprocess
import tempfile
from vosk import Model, KaldiRecognizer
import logging

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """
    Класс для обработки аудио и распознавания речи через Vosk
    """

    def __init__(self, model_path=None):
        """
        Инициализация Vosk модели

        Args:
            model_path: путь к модели Vosk (если None, использует vosk-model-small-ru-0.22)
        """
        if model_path is None:
            # Путь к модели по умолчанию
            model_path = os.path.join(
                os.path.dirname(__file__),
                "vosk-model-small-ru-0.22"
            )

        if not os.path.exists(model_path):
            logger.warning(f"⚠️ Модель не найдена по пути: {model_path}")
            logger.info("📥 Пожалуйста, скачайте модель с https://alphacephei.com/vosk/models")
            self.model = None
        else:
            logger.info(f"📂 Загрузка модели из: {model_path}")
            self.model = Model(model_path)
            logger.info("✅ Модель успешно загружена")

    def convert_to_wav(self, input_path):
        """
        Конвертация аудио в WAV формат (16kHz, mono, 16-bit)

        Args:
            input_path: путь к входному аудио файлу

        Returns:
            путь к сконвертированному WAV файлу
        """
        # Создание временного файла для WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
            output_path = temp_wav.name

        try:
            # Конвертация через ffmpeg
            command = [
                'ffmpeg',
                '-i', input_path,
                '-ar', '16000',  # Sample rate 16kHz
                '-ac', '1',      # Mono
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-y',            # Overwrite output file
                output_path
            ]

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )

            if result.returncode != 0:
                raise Exception(f"FFmpeg ошибка: {result.stderr.decode()}")

            logger.info(f"✅ Аудио сконвертировано: {output_path}")
            return output_path

        except subprocess.TimeoutExpired:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise Exception("Таймаут конвертации аудио (>10 секунд)")

        except Exception as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise e

    def recognize_audio(self, audio_path):
        """
        Распознавание речи из аудио файла

        Args:
            audio_path: путь к аудио файлу

        Returns:
            распознанный текст (строка)
        """
        if not self.model:
            raise Exception("Vosk модель не загружена")

        # Конвертация в WAV если нужно
        if not audio_path.endswith('.wav'):
            wav_path = self.convert_to_wav(audio_path)
            delete_wav = True
        else:
            wav_path = audio_path
            delete_wav = False

        try:
            # Открытие WAV файла
            wf = wave.open(wav_path, "rb")

            # Проверка формата
            if wf.getnchannels() != 1:
                raise Exception("Аудио должно быть моно (1 канал)")

            sample_rate = wf.getframerate()
            if sample_rate not in [8000, 16000, 32000, 48000]:
                logger.warning(f"⚠️ Необычный sample rate: {sample_rate} Hz")

            # Создание распознавателя
            recognizer = KaldiRecognizer(self.model, sample_rate)
            recognizer.SetWords(True)

            # Обработка аудио по частям
            full_result = ""

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if 'text' in result and result['text']:
                        full_result += result['text'] + " "

            # Финальный результат
            final_result = json.loads(recognizer.FinalResult())
            if 'text' in final_result and final_result['text']:
                full_result += final_result['text']

            wf.close()

            # Очистка текста
            transcription = full_result.strip().lower()

            logger.info(f"🎤 Распознано: '{transcription}'")

            return transcription

        finally:
            # Удаление временного WAV файла
            if delete_wav and os.path.exists(wav_path):
                os.remove(wav_path)

    def normalize_text(self, text):
        """
        Нормализация текста для сравнения (удаление ударений, пробелов, приведение к нижнему регистру)

        Args:
            text: исходный текст

        Returns:
            нормализованный текст
        """
        # Удаление ударений (́)
        text = text.replace('́', '')

        # Приведение к нижнему регистру
        text = text.lower()

        # Удаление лишних пробелов
        text = ' '.join(text.split())

        return text

    def calculate_accuracy(self, spoken, expected):
        """
        Расчет точности произношения (процент совпадения)

        Args:
            spoken: распознанный текст
            expected: ожидаемый текст

        Returns:
            процент точности (0-100)
        """
        # Нормализация текстов
        spoken_normalized = self.normalize_text(spoken)
        expected_normalized = self.normalize_text(expected)

        # Точное совпадение
        if spoken_normalized == expected_normalized:
            return 100

        # Разбивка на слова
        spoken_words = spoken_normalized.split()
        expected_words = expected_normalized.split()

        if not expected_words:
            return 0

        # Подсчет совпавших слов
        matched = 0
        for word in expected_words:
            if word in spoken_words:
                matched += 1

        # Процент совпадения
        accuracy = int((matched / len(expected_words)) * 100)

        return accuracy

    def get_feedback(self, accuracy):
        """
        Получение текстовой обратной связи по точности

        Args:
            accuracy: процент точности (0-100)

        Returns:
            текстовая обратная связь
        """
        if accuracy == 100:
            return "Отлично! Идеальное произношение! 🌟"
        elif accuracy >= 80:
            return "Очень хорошо! Небольшие неточности. 👍"
        elif accuracy >= 60:
            return "Хорошо! Продолжайте практиковаться. 💪"
        elif accuracy >= 40:
            return "Неплохо, но нужно улучшить произношение. 🔄"
        else:
            return "Попробуйте еще раз! Слушайте внимательно. 🎯"

    def evaluate_pronunciation(self, spoken, expected):
        """
        Оценка произношения

        Args:
            spoken: распознанный текст
            expected: ожидаемый текст

        Returns:
            (accuracy, feedback) - кортеж с точностью и обратной связью
        """
        accuracy = self.calculate_accuracy(spoken, expected)
        feedback = self.get_feedback(accuracy)

        return accuracy, feedback


# Тестирование (если запускается напрямую)
if __name__ == "__main__":
    print("🧪 Тестирование VoiceProcessor...")

    processor = VoiceProcessor()

    # Тест нормализации
    test_cases = [
        ("МАМА", "мама", 100),
        ("МА́МА", "мама", 100),
        ("мама", "МАМА", 100),
        ("кот", "кошка", 0),
        ("мама папа", "мама", 50),
    ]

    for spoken, expected, expected_accuracy in test_cases:
        accuracy = processor.calculate_accuracy(spoken, expected)
        print(f"Сказано: '{spoken}', Ожидалось: '{expected}' → Точность: {accuracy}% (ожидалось {expected_accuracy}%)")
        assert accuracy == expected_accuracy, f"Ошибка: ожидалось {expected_accuracy}%, получено {accuracy}%"

    print("✅ Все тесты пройдены!")
