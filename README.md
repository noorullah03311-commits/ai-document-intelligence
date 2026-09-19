# AI Document Intelligence

## Week 3 - Better Document Understanding

An AI-based document processing application that can read PDF and image documents, classify them, and extract important information.

## Features

- PDF document reading
- OCR for scanned/image documents
- Image preprocessing
- Text cleaning and normalization
- Document classification
- Invoice field extraction
- Resume field extraction
- Missing field handling
- Machine learning classification
- Model comparison
- Confidence display

## Project Flow

Upload Document
        ↓
Read Text / OCR
        ↓
Clean Text
        ↓
Identify Document Type
        ↓
Extract Fields
        ↓
Check Missing Fields
        ↓
Show Result

## Dataset

The Week 3 dataset contains 15 PDF documents:

- Invoice: 5 documents
- Resume: 5 documents
- Other: 5 documents

Dataset structure:

dataset/
└── week3_dataset/
    ├── Invoice/
    ├── Resume/
    └── Other/

## Text Preprocessing

The application cleans extracted text by:

- Removing extra spaces
- Removing repeated blank lines
- Cleaning empty lines
- Joining words split across lines
- Normalizing extracted text

## OCR Improvements

For scanned documents and images, the application performs:

- Grayscale conversion
- Image resizing
- Contrast enhancement
- Thresholding
- Tesseract OCR

## Machine Learning

TF-IDF is used to convert document text into numerical features.

Two models were compared:

1. Logistic Regression
2. Multinomial Naive Bayes

## Model Evaluation

The models were evaluated using:

- Accuracy
- Precision
- Recall
- F1-score
- Classification Report
- Confusion Matrix

### Results

| Model | Accuracy | Precision | Recall | F1-score |
|---|---:|---:|---:|---:|
| Logistic Regression | 40% | 45% | 40% | 35% |
| Naive Bayes | 60% | 47% | 60% | 50% |

The evaluation was performed on a small dataset, so the results are preliminary and may change with a larger dataset.

## Invoice Extraction

The application extracts:

- Invoice Number
- Date
- Company Name
- Total Amount
- Email
- Phone

If a required field is missing, the application displays:

`Not Found`

## Resume Extraction

The application extracts:

- Name
- Email
- Phone
- Skills

Missing fields are displayed as:

`Not Found`

## Confidence

The application displays the machine learning classification confidence when available.

Low-confidence predictions are highlighted so the result can be manually verified.

## Testing

The application was tested with:

- Invoice documents
- Resume documents
- Other documents
- Image/scanned documents
- Documents with missing fields

## Technologies Used

- Python
- Streamlit
- PyMuPDF
- Tesseract OCR
- Pillow
- Scikit-learn
- TF-IDF
- Logistic Regression
- Multinomial Naive Bayes

## Files

```text
ai-document-intelligence/
│
├── dataset/
│   ├── Invoice/
│   ├── Other/
│   ├── Resume/
│   └── week3_dataset/
│
├── app.py
├── train_model.py
├── README.md
└── requirements.txt