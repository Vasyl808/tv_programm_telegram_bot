import os

from typing import Tuple, List

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

import joblib
import numpy as np
from PIL import Image


def load_images_from_folder(folder: str, label: int, target_size=(64, 64)) -> Tuple[List[np.array], List[int]]:
    images = []
    labels = []
    for filename in os.listdir(folder):
        img_path = os.path.join(folder, filename)
        if not os.path.isfile(img_path):
            print(f"Файл не знайдено: {img_path}")
            continue
        try:
            with Image.open(img_path) as img:
                img = img.convert('L')
                img_resized = img.resize(target_size)
                img_array = np.array(img_resized).flatten()
                images.append(img_array)
                labels.append(label)
        except Exception as e:
            print(f"Не вдалося відкрити зображення {img_path}: {e}")
    return images, labels


if __name__ == '__main__':
    zero_images, zero_labels = load_images_from_folder('zeros', 0)
    five_images, five_labels = load_images_from_folder('fives', 5)

    X = np.array(zero_images + five_images)
    y = np.array(zero_labels + five_labels)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LogisticRegression()
    model.fit(X_train, y_train)

    joblib.dump(model, 'logistic_regression_model.pkl')
    loaded_model = joblib.load('logistic_regression_model.pkl')

    y_pred = loaded_model.predict(X_test)

    print(f"Accuracy: {accuracy_score(y_test, y_pred)}")
    print(classification_report(y_test, y_pred))
