import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

DATASET_PATH = "dataset/week3_dataset"
CATEGORIES = ["Invoice", "Other", "Resume"]


def _load_training_data():
    texts, labels = [], []
    if not os.path.exists(DATASET_PATH):
        return texts, labels
    for category in CATEGORIES:
        folder = os.path.join(DATASET_PATH, category)
        if not os.path.isdir(folder):
            continue
        for filename in os.listdir(folder):
            if not filename.lower().endswith(".txt"):
                continue
            path = os.path.join(folder, filename)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    text = file.read().strip()
                if text:
                    texts.append(text)
                    labels.append(category)
            except OSError:
                continue
    return texts, labels


def classify_document(text):
    training_texts, training_labels = _load_training_data()
    if len(training_texts) < 2 or len(set(training_labels)) < 2:
        return "Other", None, {}
    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(training_texts)
    model = MultinomialNB()
    model.fit(X, training_labels)
    vector = vectorizer.transform([text])
    prediction = model.predict(vector)[0]
    probabilities = model.predict_proba(vector)[0]
    confidence = float(max(probabilities))
    probability_map = {
        label: float(prob)
        for label, prob in zip(model.classes_, probabilities)
    }
    return prediction, confidence, probability_map
