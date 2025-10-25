/**
 * Vosk Backend Integration для Russian Learning Platform
 *
 * Этот модуль интегрирует Vosk speech recognition backend с frontend приложением
 * Предоставляет функции для:
 * - Записи аудио через MediaRecorder
 * - Отправки аудио на Vosk backend
 * - Получения оценки произношения
 * - Fallback на Web Speech API если backend недоступен
 */

class VoskIntegration {
    constructor(backendUrl) {
        // URL backend API (замените после деплоя на Render.com)
        this.backendUrl = backendUrl || 'https://russian-speech-recognition.onrender.com';

        // MediaRecorder для записи аудио
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;

        // Статус backend
        this.backendAvailable = null; // null = не проверено, true/false
        this.lastHealthCheck = 0;
        this.healthCheckInterval = 60000; // Проверять каждую минуту

        console.log(`🎤 Vosk Integration инициализирован: ${this.backendUrl}`);
    }

    /**
     * Проверка доступности backend
     */
    async checkBackendHealth() {
        const now = Date.now();

        // Если недавно проверяли, используем кэш
        if (this.backendAvailable !== null && (now - this.lastHealthCheck) < this.healthCheckInterval) {
            return this.backendAvailable;
        }

        try {
            console.log('🔍 Проверка доступности Vosk backend...');

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 секунд таймаут

            const response = await fetch(`${this.backendUrl}/health`, {
                method: 'GET',
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                const data = await response.json();
                this.backendAvailable = data.status === 'ok' || data.status === 'healthy';
                this.lastHealthCheck = now;
                console.log('✅ Vosk backend доступен');
                return this.backendAvailable;
            } else {
                this.backendAvailable = false;
                console.log('⚠️ Vosk backend недоступен (статус не ok)');
                return false;
            }
        } catch (error) {
            this.backendAvailable = false;
            this.lastHealthCheck = now;
            console.log('⚠️ Vosk backend недоступен:', error.message);
            return false;
        }
    }

    /**
     * Начать запись аудио
     */
    async startRecording() {
        try {
            // Запрос доступа к микрофону
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1, // моно
                    sampleRate: 16000, // 16kHz
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            // Создание MediaRecorder
            // Используем webm для лучшей совместимости
            const options = { mimeType: 'audio/webm' };

            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                // Fallback на другой формат
                options.mimeType = 'audio/ogg';
            }

            this.mediaRecorder = new MediaRecorder(stream, options);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                console.log('🎤 Запись завершена');
            };

            this.mediaRecorder.start();
            this.isRecording = true;

            console.log('🎤 Запись началась');
            return true;

        } catch (error) {
            console.error('❌ Ошибка доступа к микрофону:', error);
            throw new Error('Не удалось получить доступ к микрофону');
        }
    }

    /**
     * Остановить запись аудио
     */
    async stopRecording() {
        return new Promise((resolve, reject) => {
            if (!this.mediaRecorder || !this.isRecording) {
                reject(new Error('Запись не начата'));
                return;
            }

            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, {
                    type: this.mediaRecorder.mimeType
                });

                // Остановка всех треков микрофона
                this.mediaRecorder.stream.getTracks().forEach(track => track.stop());

                this.isRecording = false;
                console.log(`🎤 Аудио записано: ${(audioBlob.size / 1024).toFixed(2)} KB`);

                resolve(audioBlob);
            };

            this.mediaRecorder.stop();
        });
    }

    /**
     * Отправить аудио на backend для транскрипции
     */
    async transcribe(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');

            console.log('📤 Отправка аудио на Vosk backend...');

            const response = await fetch(`${this.backendUrl}/transcribe`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Ошибка транскрипции');
            }

            console.log('✅ Транскрипция получена:', result.transcription);

            return result.transcription;

        } catch (error) {
            console.error('❌ Ошибка транскрипции:', error);
            throw error;
        }
    }

    /**
     * Оценить произношение
     */
    async evaluate(audioBlob, expectedText) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            formData.append('expected', expectedText);

            console.log(`📤 Отправка на оценку: ожидается "${expectedText}"`);

            const response = await fetch(`${this.backendUrl}/evaluate`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Ошибка оценки');
            }

            console.log(`✅ Оценка получена: ${result.accuracy}% - "${result.transcription}"`);

            return {
                transcription: result.transcription,
                expected: result.expected,
                accuracy: result.accuracy,
                feedback: result.feedback
            };

        } catch (error) {
            console.error('❌ Ошибка оценки:', error);
            throw error;
        }
    }

    /**
     * Запись и оценка произношения (all-in-one функция)
     */
    async recordAndEvaluate(expectedText, onProgress = null) {
        try {
            // 1. Проверка backend
            if (onProgress) onProgress('Проверка backend...');
            const backendOk = await this.checkBackendHealth();

            if (!backendOk) {
                throw new Error('BACKEND_UNAVAILABLE');
            }

            // 2. Начало записи
            if (onProgress) onProgress('Говорите сейчас...');
            await this.startRecording();

            // Вернуть промис, который разрешится когда запись остановится
            return new Promise((resolve, reject) => {
                // Сохранить функции resolve/reject для использования в stopAndEvaluate
                this._pendingEvaluation = { resolve, reject, expectedText, onProgress };
            });

        } catch (error) {
            console.error('❌ Ошибка записи и оценки:', error);
            throw error;
        }
    }

    /**
     * Остановить запись и получить оценку
     */
    async stopAndEvaluate() {
        if (!this._pendingEvaluation) {
            throw new Error('Нет активной записи');
        }

        const { resolve, reject, expectedText, onProgress } = this._pendingEvaluation;

        try {
            // 3. Остановка записи
            if (onProgress) onProgress('Обработка аудио...');
            const audioBlob = await this.stopRecording();

            // 4. Отправка на оценку
            if (onProgress) onProgress('Анализ произношения...');
            const result = await this.evaluate(audioBlob, expectedText);

            // 5. Возврат результата
            if (onProgress) onProgress('Готово!');

            this._pendingEvaluation = null;
            resolve(result);

        } catch (error) {
            this._pendingEvaluation = null;
            reject(error);
        }
    }

    /**
     * Отменить текущую запись
     */
    cancelRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            this.isRecording = false;
            this.audioChunks = [];
        }

        if (this._pendingEvaluation) {
            this._pendingEvaluation.reject(new Error('Запись отменена'));
            this._pendingEvaluation = null;
        }
    }
}

// Экспорт для использования в других скриптах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoskIntegration;
}
