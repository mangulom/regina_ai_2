import joblib
import os
import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline


MODEL_FILE = "intent_model.joblib"
DATASET_FILE = "intent_dataset.json"


class IntentModel:

    def __init__(self):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2)
            )),
            ("clf", SGDClassifier(random_state=42))
        ])

    def train(self, texts, labels):
        self.pipeline.fit(texts, labels)

    def predict(self, text: str):
        return self.pipeline.predict([text])[0]

    def save(self):
        joblib.dump(self.pipeline, MODEL_FILE)

    def load(self):
        self.pipeline = joblib.load(MODEL_FILE)


def load_dataset():

    if not os.path.exists(DATASET_FILE):
        return [], []

    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = [x["text"] for x in data]
    labels = [x["label"] for x in data]

    return texts, labels


def save_example(text, label):

    data = []

    if os.path.exists(DATASET_FILE):
        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    data.append({
        "text": text,
        "label": label
    })

    with open(DATASET_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def retrain_model():

    texts, labels = load_dataset()

    if len(texts) < 2:
        raise Exception("No hay suficientes ejemplos para reentrenar")

    model = IntentModel()
    model.train(texts, labels)
    model.save()

    return model

def load_or_create_model():

    if os.path.exists(MODEL_FILE):
        model = IntentModel()
        model.load()
        return model

    texts, labels = load_dataset()

    if len(texts) == 0:
        texts = [
            "ordenes de pago",
            "lista de ordenes de pago",
            "quiero ver ordenes de pago",
            "mis ordenes",
            "usuarios",
            "listar usuarios",
            "ver usuarios"
        ]

        labels = [
            "ORDENES_PAGO",
            "ORDENES_PAGO",
            "ORDENES_PAGO",
            "ORDENES_PAGO",
            "USUARIOS",
            "USUARIOS",
            "USUARIOS"
        ]

        model = IntentModel()
        model.train(texts, labels)
        model.save()
        return model

    model = IntentModel()
    model.train(texts, labels)
    model.save()
    return model