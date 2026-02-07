import os
import json
import joblib
import re
from typing import List, Tuple

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "intent_model.joblib")
DATA_PATH = os.path.join(BASE_DIR, "intent_examples.json")


# ----------------------------
# normalización
# ----------------------------
def normalize_text(text: str) -> str:
    text = text.lower().strip()

    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text


# ----------------------------
# dataset base
# ----------------------------
DEFAULT_DATA = [
    # ORDENES DE PAGO
    ("ordenes de pago", "ORDENES_PAGO"),
    ("lista de ordenes de pago", "ORDENES_PAGO"),
    ("listado de ordenes de pago", "ORDENES_PAGO"),
    ("ver ordenes de pago", "ORDENES_PAGO"),
    ("consultar ordenes de pago", "ORDENES_PAGO"),
    ("ordenes", "ORDENES_PAGO"),
    ("listar ordenes", "ORDENES_PAGO"),
    ("lista de ordenes", "ORDENES_PAGO"),

    # USUARIOS
    ("usuarios", "USUARIOS"),
    ("lista de usuarios", "USUARIOS"),
    ("listado de usuarios", "USUARIOS"),
    ("ver usuarios", "USUARIOS"),
    ("consultar usuarios", "USUARIOS"),
    ("mostrar usuarios", "USUARIOS"),
    ("listar usuarios", "USUARIOS"),
]


# ----------------------------
# carga ejemplos
# ----------------------------
def load_examples() -> List[Tuple[str, str]]:

    data = list(DEFAULT_DATA)

    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            user_data = json.load(f)

        for item in user_data:
            data.append((item["text"], item["intent"]))

    return data


# ----------------------------
# guardar ejemplo nuevo
# ----------------------------
def save_example(text: str, intent: str):

    text = normalize_text(text)

    examples = []

    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            examples = json.load(f)

    examples.append({
        "text": text,
        "intent": intent
    })

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(examples, f, ensure_ascii=False, indent=2)


# ----------------------------
# entrenamiento
# ----------------------------
def train_model():

    data = load_examples()

    X = [normalize_text(t) for t, _ in data]
    y = [label for _, label in data]

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1
        )),
        ("clf", LogisticRegression(max_iter=2000))
    ])

    pipeline.fit(X, y)

    joblib.dump(pipeline, MODEL_PATH)

    return pipeline


# ----------------------------
# cargar o crear
# ----------------------------
def load_or_create_model():

    if os.path.exists(MODEL_PATH):
        return IntentModel(joblib.load(MODEL_PATH))

    model = train_model()
    return IntentModel(model)


# ----------------------------
# reentrenar
# ----------------------------
def retrain_model():

    model = train_model()
    return IntentModel(model)


# ----------------------------
# wrapper del modelo
# ----------------------------
class IntentModel:

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def predict(self, text: str) -> Tuple[str, float]:

        text_n = normalize_text(text)

        proba = self.pipeline.predict_proba([text_n])[0]
        classes = self.pipeline.classes_

        idx = proba.argmax()

        intent = classes[idx]
        score = float(proba[idx])

        return intent, score
