import time
import subprocess
from ppadb.client import Client as AdbClient
from PIL import Image
import pytesseract
import cv2
import numpy as np
import random

# Укажите путь к Tesseract, если он установлен в нестандартном месте
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Подключение к ADB
def connect_devices():
    adb = AdbClient(host='127.0.0.1', port=5037)
    devices = adb.devices()

    if len(devices) == 0:
        print("Нет подключенных устройств")
        return []
    else:
        print(f"Подключено устройств: {len(devices)}")
        return devices

# Запуск Telegram с игровым приложением для каждого устройства
def launch_telegram_game(device):
    print(f"Запуск Telegram с игрой на устройстве {device.serial}")
    device.shell('am start -n org.telegram.messenger/org.telegram.ui.LaunchActivity')
    time.sleep(5)
    
    # Переход по ссылке на игру с случайными координатами
    x_coord = random.randint(500, 800)
    y_coord = random.randint(500, 800)
    device.shell(f'am start -a android.intent.action.VIEW -d "https://t.me/notpixel/app?startapp=x{x_coord}_y{y_coord}"')
    time.sleep(20)  # Ждем, пока игра загрузится

# Имитация нажатия на экран с небольшими случайными вариациями
def tap_on_screen(device, x, y):
    x_random = x + random.randint(-4, 4)
    y_random = y + random.randint(-4, 4)
    print(f"Нажатие на экран на устройстве {device.serial} в координатах: ({x_random}, {y_random})")
    device.shell(f'input tap {x_random} {y_random}')
    time.sleep(random.uniform(1, 3))  # Случайная задержка перед следующим действием

# Сделать скриншот экрана
def take_screenshot(device):
    print(f"Делаем скриншот на устройстве {device.serial}...")
    result = device.screencap()
    with open(f'screenshot_{device.serial}.png', 'wb') as fp:
        fp.write(result)
    print(f"Скриншот сохранен для устройства {device.serial}")
    return cv2.imread(f'screenshot_{device.serial}.png')

# Распознавание текста на экране и возвращение его координат
def extract_text_with_boxes(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    text_boxes = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)

    for i, text in enumerate(text_boxes['text']):
        if "Paint" in text:
            x, y, w, h = text_boxes['left'][i], text_boxes['top'][i], text_boxes['width'][i], text_boxes['height'][i]
            print(f"Кнопка 'Paint' найдена! Координаты: ({x}, {y}, {w}, {h})")
            return x + w // 2, y + h // 2  # Возвращаем центральную точку кнопки
    print("Кнопка 'Paint' не найдена.")
    return None

# Основной процесс
def main():
    devices = connect_devices()
    
    if devices:
        while True:
            for device in devices:
                launch_telegram_game(device)
                retries = 3
                
                while retries > 0:
                    screenshot = take_screenshot(device)
                    paint_coords = extract_text_with_boxes(screenshot)

                    if paint_coords:
                        print(f"Нажимаем на кнопку 'Paint' по координатам {paint_coords} на устройстве {device.serial}")
                        tap_on_screen(device, *paint_coords)

                        time.sleep(3)
                        screenshot = take_screenshot(device)

                        if not extract_text_with_boxes(screenshot):
                            print(f"Кнопка 'Paint' исчезла на устройстве {device.serial}, переходим к следующему устройству.")
                            break
                    else:
                        print(f"Кнопка 'Paint' не найдена на устройстве {device.serial}. Осталось попыток: {retries-1}")
                        retries -= 1
                        time.sleep(30)

            print("Все устройства проверены. Ждем 10 минут перед повторной проверкой.")
            time.sleep(600)  # Ожидание 10 минут перед новым циклом

if __name__ == "__main__":
    main()
