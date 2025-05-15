import os
import requests
import pyttsx3
import sounddevice as sd
import numpy as np
from vosk import Model, KaldiRecognizer
import queue
import json
import sys
import zipfile

class VoiceAssistant:
    def __init__(self):
        # Проверка и распаковка модели Vosk
        model_zip = "vosk-model-small-ru-0.22.zip"
        model_path = "vosk-model-small-ru-0.22"
        
        if not os.path.exists(model_path):
            if os.path.exists(model_zip):
                print("Распаковываю модель Vosk...")
                try:
                    with zipfile.ZipFile(model_zip, 'r') as zip_ref:
                        zip_ref.extractall(model_path)
                    print("Модель успешно распакована")
                except Exception as e:
                    print(f"Ошибка при распаковке модели: {str(e)}")
                    exit(1)
            else:
                print(f"Файл модели {model_zip} не найден. Пожалуйста, скачайте его с https://alphacephei.com/vosk/models")
                exit(1)
        
        # Инициализация движка для синтеза речи
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)
        
        self.current_text = ""
        
        # Инициализация модели Vosk
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        
        # Очередь для аудиоданных
        self.audio_queue = queue.Queue()
    
    # ... (остальные методы класса остаются без изменений)
    def speak(self, text):
        """Произносит переданный текст"""
        print(f"Ассистент: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
        
    def audio_callback(self, indata, frames, time, status):
        """Callback функция для получения аудио"""
        if status:
            print(status, file=sys.stderr)
        self.audio_queue.put(bytes(indata))
        
    def listen(self):
        """Слушает и распознает голосовые команды"""
        print("Слушаю...")
        
        # Настройки аудиопотока
        samplerate = 16000
        device = sd.default.device
        channels = 1
        dtype = 'int16'
        
        with sd.RawInputStream(samplerate=samplerate, blocksize=8000,
                             device=device, channels=channels,
                             dtype=dtype, callback=self.audio_callback):
            while True:
                data = self.audio_queue.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    command = result.get("text", "").lower()
                    if command:
                        print(f"Распознано: {command}")
                        return command
        return ""
    
    def get_text_from_web(self):
        """Получает текст с сайта loripsum.net"""
        try:
            response = requests.get("https://loripsum.net/api/10/short/headers")
            if response.status_code == 200:
                self.current_text = response.text
                self.speak("Текст успешно получен с сайта")
            else:
                self.speak("Ошибка при получении текста с сайта")
        except Exception as e:
            self.speak(f"Ошибка при запросе к сайту: {str(e)}")
            
    def read_text(self):
        """Читает текущий текст вслух"""
        if self.current_text:
            self.speak("Читаю текст")
            # Читаем только первые 200 символов, чтобы не перегружать TTS
            self.engine.say(self.current_text[:200])
            self.engine.runAndWait()
        else:
            self.speak("Нет текста для чтения. Сначала получите текст командой 'создать'")
            
    def save_as_html(self):
        """Сохраняет текущий текст как HTML файл"""
        if self.current_text:
            try:
                with open("output.html", "w", encoding="utf-8") as f:
                    f.write(self.current_text)
                self.speak("Текст сохранен как HTML файл")
            except Exception as e:
                self.speak(f"Ошибка при сохранении HTML: {str(e)}")
        else:
            self.speak("Нет текста для сохранения. Сначала получите текст командой 'создать'")
            
    def save_as_text(self):
        """Сохраняет текущий текст как обычный текстовый файл"""
        if self.current_text:
            try:
                # Удаляем HTML теги для чистого текста
                clean_text = " ".join(self.current_text.split())
                with open("output.txt", "w", encoding="utf-8") as f:
                    f.write(clean_text)
                self.speak("Текст сохранен как текстовый файл")
            except Exception as e:
                self.speak(f"Ошибка при сохранении текста: {str(e)}")
        else:
            self.speak("Нет текста для сохранения. Сначала получите текст командой 'создать'")
            
    def process_command(self, command):
        """Обрабатывает распознанную команду"""
        if "созда" in command:
            self.get_text_from_web()
        elif "прочита" in command or "прочесть" in command:
            self.read_text()
        elif "сохрани html" in command or "сохранить html" in command:
            self.save_as_html()
        elif "сохрани текст" in command or "сохранить текст" in command:
            self.save_as_text()
        elif "выход" in command or "закончи" in command:
            self.speak("До свидания!")
            return False
        else:
            self.speak("Не распознал команду. Пожалуйста, повторите.")
        return True
        
    def run(self):
        """Основной цикл работы ассистента"""
        self.speak("Голосовой ассистент запущен. Доступные команды: создать, прочесть, сохранить html, сохранить текст")
        
        running = True
        while running:
            command = self.listen()
            if command:
                running = self.process_command(command)

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()