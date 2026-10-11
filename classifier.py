"""Cached TF-IDF + Naive Bayes document classifier.

Training examples are read from dataset/week3_dataset/<Invoice|Resume|Other>/*.txt.
If that dataset is absent, a small bundled fallback corpus keeps the demo usable;
real project evaluation should use representative, labeled training documents.
"""
from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset" / "week3_dataset"
CATEGORIES = ("Invoice", "Other", "Resume")

_FALLBACK = {
    "Invoice": [
        "Invoice invoice number billing date company total amount payment due subtotal tax balance",
        "Receipt invoice number purchase quantity unit price total amount vendor payment date",
        "Bill to company invoice id item description amount due payment terms",
    ],
    "Resume": [
        "Resume curriculum vitae professional experience education skills projects email phone",
        "Candidate profile work experience technical skills qualifications education history",
        "CV software engineer skills Python SQL experience university projects contact",
    ],
    "Other": [
        "General document notice announcement meeting minutes policy information details",
        "Agreement contract terms and conditions parties obligations signature",
        "Purchase order request form department delivery items instructions",
    ],
}


def _load_training_data():
    texts, labels = [], []
    if DATASET_PATH.is_dir():
        for category in CATEGORIES:
            folder = DATASET_PATH / category
            if not folder.is_dir():
                continue
            for path in sorted(folder.glob("*.txt")):
                try:
                    text = path.read_text(encoding="utf-8").strip()
                except (OSError, UnicodeError):
                    continue
                if text:
                    texts.append(text)
                    labels.append(category)
    if len(texts) < 3 or len(set(labels)) < 2:
        texts = [text for category in CATEGORIES for text in _FALLBACK[category]]
        labels = [category for category in CATEGORIES for _ in _FALLBACK[category]]
    return texts, labels


@lru_cache(maxsize=1)
def _get_model():
    texts, labels = _load_training_data()
    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), strip_accents="unicode")
    matrix = vectorizer.fit_transform(texts)
    model = MultinomialNB()
    model.fit(matrix, labels)
    return vectorizer, model


def clear_model_cache():
    """Clear the cached model after changing training data."""
    _get_model.cache_clear()


def classify_document(text):
    if not isinstance(text, str) or not text.strip():
        return "Other", None, {}
    vectorizer, model = _get_model()
    vector = vectorizer.transform([text])
    prediction = str(model.predict(vector)[0])
    probabilities = model.predict_proba(vector)[0]
    confidence = float(max(probabilities))
    probability_map = {str(label): float(prob) for label, prob in zip(model.classes_, probabilities)}
    return prediction, confidence, probability_map
