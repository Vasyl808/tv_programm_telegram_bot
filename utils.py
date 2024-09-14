import json

import joblib
import numpy as np

import requests

from PIL import Image
from io import BytesIO

from typing import Union

from parse import (
    parse,
    get_available_days,
    get_program,
    get_program_elements
)


class JSONLoader:
    @staticmethod
    def load(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Помилка: Файл {file_path} не знайдено.")
        except json.JSONDecodeError:
            print(f"Помилка: Не вдалося розпізнати JSON у файлі {file_path}.")
        except Exception as e:
            print(f"Сталася непередбачувана помилка: {e}")
        return None


class ChannelParser:
    def __init__(self, website_url):
        self.website_url = website_url
        self.soup_obj = parse(website_url)

    def get_available_days(self):
        return [
            translate_text_to_ukrainian(day.get_text(strip=True))
            for day in get_available_days(self.soup_obj)
        ]

    def get_tv_schedule(self, days):
        return {
            day: "\n".join(get_program(get_program_elements(day_obj)))
            for day, day_obj in zip(days, get_available_days(self.soup_obj))
        }


def download_image(url: str, image_name_with_extension: str) -> None:
    with open(image_name_with_extension, 'wb') as handle:
        response = requests.get(url, stream=True)

        if response.status_code != 200:
            print(response.status_code)

        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)


def load_image_from_url(url: str, target_size=(64, 64)) -> Union[np.ndarray, None]:
    try:
        response = requests.get(url)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))
        img = img.convert('L')

        img_resized = img.resize(target_size)
        img_array = np.array(img_resized).flatten()

        return img_array
    except Exception as e:
        print(f"Не вдалося завантажити зображення з {url}: {e}")
        return None


def predict_number(url: str) -> str:
    image = load_image_from_url(url)

    if image is not None:
        loaded_model = joblib.load('logistic_regression_model.pkl')
        image = image.reshape(1, -1)
        result = loaded_model.predict(image)

        return str(result[0])
    else:
        print("Не вдалося завантажити зображення.")
        return '?'


def translate_day_to_ukrainian(day: str) -> str:
    translation_dict = {
        "Понедельник": "Понеділок",
        "Вторник": "Вівторок",
        "Среда": "Середа",
        "Четверг": "Четвер",
        "Пятница": "П'ятниця",
        "Суббота": "Субота",
        "Воскресенье": "Неділя"
    }

    return translation_dict.get(day, "Невідомий день")


def translate_month_to_ukrainian(month: str) -> str:
    translation_dict = {
        "января": "Січня",
        "февраля": "Лютого",
        "марта": "Березня",
        "апреля": "Квітня",
        "мая": "Травня",
        "июня": "Червня",
        "июля": "Липня",
        "августа": "Серпня",
        "сентября": "Вересня",
        "октября": "Жовтня",
        "ноября": "Листопада",
        "декабря": "Грудня"
    }

    return translation_dict.get(month, "Невідомий місяць")


def translate_text_to_ukrainian(text: str) -> str:
    parts = text.split(", ")
    day_of_week = parts[0]
    date_parts = parts[1].split(" ")

    translated_day = translate_day_to_ukrainian(day_of_week)
    translated_month = translate_month_to_ukrainian(date_parts[1])

    translated_text = f"{translated_day}, {date_parts[0]} {translated_month}"

    return translated_text
