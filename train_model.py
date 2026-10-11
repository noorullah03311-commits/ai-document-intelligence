import os
import re
import fitz

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

DATASET_PATH = "dataset/week3_dataset"
CATEGORIES = ["Invoice", "Other", "Resume"]


def clean_text(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def load_dataset():
    texts, labels = [], []
    for category in CATEGORIES:
        folder = os.path.join(DATASET_PATH, category)
        if not os.path.isdir(folder):
            continue
        for filename in os.listdir(folder):
            if not filename.lower().endswith(".pdf"):
                continue
            path = os.path.join(folder, filename)
            try:
                document = fitz.open(path)
                text = "\n".join(page.get_text() for page in document)
                document.close()
                text = clean_text(text)
                if len(text) > 20:
                    texts.append(text)
                    labels.append(category)
            except Exception as exc:
                print(f"Error reading {filename}: {exc}")
    return texts, labels


def evaluate(name, actual, predictions):
    print(f"\n{name}")
    print(f"Accuracy : {accuracy_score(actual, predictions):.2f}")
    print(f"Precision: {precision_score(actual, predictions, average='weighted', zero_division=0):.2f}")
    print(f"Recall   : {recall_score(actual, predictions, average='weighted', zero_division=0):.2f}")
    print(f"F1-score : {f1_score(actual, predictions, average='weighted', zero_division=0):.2f}")


def main():
    texts, labels = load_dataset()
    print("Total documents:", len(texts))
    for category in CATEGORIES:
        print(f"{category}: {labels.count(category)}")

    if len(texts) < 6 or len(set(labels)) < 2:
        print("Not enough data for a reliable train/test split.")
        return

    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(texts)
    X_train, X_test, y_train, y_test = train_test_split(
        X, labels, test_size=0.30, random_state=42, stratify=labels
    )

    logistic = LogisticRegression(max_iter=1000)
    logistic.fit(X_train, y_train)
    evaluate("Logistic Regression", y_test, logistic.predict(X_test))

    naive_bayes = MultinomialNB()
    naive_bayes.fit(X_train, y_train)
    evaluate("Naive Bayes", y_test, naive_bayes.predict(X_test))

    print("\nModel training/evaluation complete.")


if __name__ == "__main__":
    main()
