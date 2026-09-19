import os
import fitz
import re

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)


# =========================================================
# SETTINGS
# =========================================================

DATASET_PATH = "dataset/week3_dataset"

categories = [
    "Invoice",
    "Other",
    "Resume"
]


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(text):

    text = text.lower()

    text = re.sub(r"\s+", " ", text)

    text = text.strip()

    return text


# =========================================================
# READ DATASET
# =========================================================

texts = []
labels = []


for category in categories:

    folder = os.path.join(
        DATASET_PATH,
        category
    )

    for filename in os.listdir(folder):

        if filename.lower().endswith(".pdf"):

            filepath = os.path.join(
                folder,
                filename
            )

            try:

                document = fitz.open(filepath)

                text = ""

                for page in document:

                    text += page.get_text()

                document.close()

                text = clean_text(text)

                if len(text) > 20:

                    texts.append(text)
                    labels.append(category)

                    print(
                        f"Loaded: {category}/{filename}"
                    )

            except Exception as e:

                print(
                    f"Error reading {filename}: {e}"
                )


# =========================================================
# DATASET INFORMATION
# =========================================================

print("\n==============================")
print("DATASET INFORMATION")
print("==============================")

print("Total documents:", len(texts))

print("Invoices:", labels.count("Invoice"))
print("Resumes:", labels.count("Resume"))
print("Other:", labels.count("Other"))


# =========================================================
# CHECK DATASET
# =========================================================

if len(texts) < 6:

    print("\nNot enough documents for training.")

    exit()


# =========================================================
# TF-IDF
# =========================================================

vectorizer = TfidfVectorizer(
    max_features=3000,
    ngram_range=(1, 2)
)

X = vectorizer.fit_transform(texts)
y = labels


# =========================================================
# TRAIN / TEST SPLIT
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.30,
    random_state=42,
    stratify=y
)


# =========================================================
# LOGISTIC REGRESSION
# =========================================================

logistic_model = LogisticRegression(
    max_iter=1000
)

logistic_model.fit(
    X_train,
    y_train
)

logistic_predictions = logistic_model.predict(
    X_test
)


# =========================================================
# NAIVE BAYES
# =========================================================

naive_bayes_model = MultinomialNB()

naive_bayes_model.fit(
    X_train,
    y_train
)

naive_predictions = naive_bayes_model.predict(
    X_test
)


# =========================================================
# EVALUATION FUNCTION
# =========================================================

def evaluate_model(
    model_name,
    actual,
    predictions
):

    accuracy = accuracy_score(
        actual,
        predictions
    )

    precision = precision_score(
        actual,
        predictions,
        average="weighted",
        zero_division=0
    )

    recall = recall_score(
        actual,
        predictions,
        average="weighted",
        zero_division=0
    )

    f1 = f1_score(
        actual,
        predictions,
        average="weighted",
        zero_division=0
    )

    print("\n==============================")
    print(model_name)
    print("==============================")

    print(
        f"Accuracy : {accuracy:.2f}"
    )

    print(
        f"Precision: {precision:.2f}"
    )

    print(
        f"Recall   : {recall:.2f}"
    )

    print(
        f"F1-score : {f1:.2f}"
    )

    print("\nClassification Report:")

    print(
        classification_report(
            actual,
            predictions,
            zero_division=0
        )
    )

    print("Confusion Matrix:")

    print(
        confusion_matrix(
            actual,
            predictions,
            labels=categories
        )
    )


# =========================================================
# COMPARE MODELS
# =========================================================

evaluate_model(
    "Logistic Regression",
    y_test,
    logistic_predictions
)


evaluate_model(
    "Naive Bayes",
    y_test,
    naive_predictions
)


# =========================================================
# SAVE BEST MODEL
# =========================================================

print("\n==============================")
print("MODEL TRAINING COMPLETE")
print("==============================")

print(
    "The evaluation results above can be used "
    "to compare the two models."
)