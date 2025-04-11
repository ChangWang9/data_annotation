# 🚀 Data Annotation System

A simple and user-friendly data annotation tool specifically designed for question-answer data, with support for mathematical formula display.

## ✨ Key Features

* 📊 Support for uploading JSONL format data for annotation
* ⏱️ Customizable countdown timer to improve annotation efficiency
* 🧮 Perfect rendering of LaTeX mathematical formulas
* 📝 Simple and intuitive "Right/Error" binary classification annotation
* 📱 Responsive design that adapts to various devices
* 🔄 Support for navigation and export of annotation results

## 🛠️ Technology Stack

* **Frontend** : HTML, CSS, JavaScript, MathJax
* **Backend** : Flask (Python)
* **Data Processing** : JSON, Markdown

## 📋 User Guide

### 1. Deploy the System

```bash
# Clone the project
git clone https://github.com/ChangWang9/data_annotation.git
cd data_annotation

# Install dependencies
pip install flask markdown2

# Start the service
python app.py
```

The system will start at http://localhost:5000

### 2. Upload Data

* Prepare a JSONL file in the correct format (each line is a JSON object)
* Click "Choose File" on the homepage to upload
* The file should include `question` and `neg_reasoning_paths` fields

### 3. Annotation Process

1. View the displayed question and answer content
2. Use the up/down scroll buttons to browse long content
3. Click "Right" or "Error" to make an annotation
4. The system automatically jumps to the next data item
5. Download the results after completing the annotations

### 4. Tips

* Click "Set Timer" to customize the annotation time for each question
* When time is up, it will automatically jump to the next question, improving efficiency
* You can click "Export Annotations" at any time to save current progress

## 📁 Project Structure

```
data_annotation/
├── app.py             # Core application logic
├── static/
│   └── style.css      # Style file
├── templates/         # HTML templates
│   ├── index.html     # Homepage
│   ├── annotate.html  # Annotation page
│   └── complete.html  # Completion page
├── uploads/           # Upload file directory
├── annotations/       # Annotation results directory
└── data_files/        # Processed data files
```

## 📝 Data Format Description

Example of the JSONL file format for upload:

```jsonl
{"question": "Question text", "neg_reasoning_paths": ["Answer text"]}
```

If the data contains LaTeX formulas, the system will automatically process and render them.
