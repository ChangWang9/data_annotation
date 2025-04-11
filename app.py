# app.py
import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import markdown2
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ANNOTATION_FOLDER'] = 'annotations'
app.config['DATA_FOLDER'] = 'data_files'

def fix_tabular_to_array(latex_text: str) -> str:
    """Convert \begin{tabular}{...} to \begin{array}{...} and \hline to \noalign{\hrule}."""
    import re
    # 1) \begin{tabular}{xxx} => \begin{array}{xxx}
    latex_text = re.sub(r'\\begin\{tabular\}(\{[^}]*\})', r'\\begin{array}\1', latex_text)
    # 2) \end{tabular} => \end{array}
    latex_text = latex_text.replace(r'\end{tabular}', r'\end{array}')
    # 3) \hline => \noalign{\hrule}
    latex_text = latex_text.replace(r'\hline', r'\noalign{\hrule}')
    return latex_text

# Ensure folders exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['ANNOTATION_FOLDER'], app.config['DATA_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    session_id = str(uuid.uuid4())
    filename = f"{session_id}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line.strip())
                if 'neg_reasoning_paths' in item:
                    question_text = item.get('question', '(No question)')
                    
                    # Get all neg_reasoning_paths instead of just the first one
                    response_texts = item.get('neg_reasoning_paths', ['(No response)'])
                    
                    # Process LaTeX in question
                    question_text = fix_tabular_to_array(question_text)
                    
                    # Process LaTeX in all responses
                    processed_responses = []
                    for response in response_texts:
                        processed_responses.append(fix_tabular_to_array(response))
                    
                    data.append({
                        'question': question_text,
                        'responses': processed_responses
                    })
            except json.JSONDecodeError:
                continue
    
    if not data:
        os.remove(filepath)
        return "No valid data found. Please check if the file format is correct", 400
    
    data_filepath = os.path.join(app.config['DATA_FOLDER'], f"{session_id}_data.json")
    with open(data_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Initialize annotations with structure for multiple answers per question
    annotations = []
    for i, item in enumerate(data):
        annotation_item = {
            "question_index": i,
            "question": item["question"],
            "responses": [],
            "annotations": [],
            "timestamp": ""
        }
        annotations.append(annotation_item)
    
    annotations_filepath = os.path.join(app.config['ANNOTATION_FOLDER'], f"{session_id}_annotations.json")
    with open(annotations_filepath, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)
    
    session['session_id'] = session_id
    session['current_question_index'] = 0
    session['current_response_index'] = 0
    session['total_questions'] = len(data)
    
    return redirect(url_for('annotate'))

@app.route('/annotate')
def annotate():
    if 'session_id' not in session:
        return redirect(url_for('index'))
    
    session_id = session['session_id']
    current_question_index = session.get('current_question_index', 0)
    current_response_index = session.get('current_response_index', 0)
    total_questions = session.get('total_questions', 0)
    
    if current_question_index >= total_questions:
        return redirect(url_for('complete'))
    
    data_filepath = os.path.join(app.config['DATA_FOLDER'], f"{session_id}_data.json")
    with open(data_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        current_question = data[current_question_index]
    
    # Get total number of responses for current question
    total_responses = len(current_question['responses'])
    
    # Check if we have annotated all responses for current question
    if current_response_index >= total_responses:
        # Move to next question
        session['current_question_index'] = current_question_index + 1
        session['current_response_index'] = 0
        return redirect(url_for('annotate'))
    
    # Convert question and current response from Markdown to HTML
    question_html = markdown2.markdown(current_question['question'], extras=["fenced-code-blocks"])
    response_html = markdown2.markdown(current_question['responses'][current_response_index], extras=["fenced-code-blocks"])

    # Create item to pass to template
    display_item = {
        'question_html': question_html,
        'response_html': response_html,
        'current_response': current_response_index + 1,
        'total_responses': total_responses
    }

    return render_template(
        'annotate.html', 
        item=display_item, 
        current_question=current_question_index + 1, 
        total_questions=total_questions,
        countdown=60
    )

@app.route('/record', methods=['POST'])
def record_annotation():
    if 'session_id' not in session:
        return jsonify({"error": "No active session"}), 400
    
    data = request.json
    is_correct = data.get('is_correct')
    
    if is_correct is None:
        return jsonify({"error": "Missing is_correct parameter"}), 400
    
    session_id = session['session_id']
    current_question_index = session.get('current_question_index', 0)
    current_response_index = session.get('current_response_index', 0)
    
    # Read data file to get the current question and response
    data_filepath = os.path.join(app.config['DATA_FOLDER'], f"{session_id}_data.json")
    with open(data_filepath, 'r', encoding='utf-8') as f:
        all_data = json.load(f)
        current_question = all_data[current_question_index]
        current_response = current_question['responses'][current_response_index]
    
    # Read existing annotations from file
    annotations_filepath = os.path.join(app.config['ANNOTATION_FOLDER'], f"{session_id}_annotations.json")
    with open(annotations_filepath, 'r', encoding='utf-8') as f:
        annotations = json.load(f)
    
    # Update the annotation for the current question and response
    if len(annotations[current_question_index]['responses']) <= current_response_index:
        # Add new response
        annotations[current_question_index]['responses'].append(current_response)
        annotations[current_question_index]['annotations'].append(is_correct)
    else:
        # Update existing response annotation
        annotations[current_question_index]['annotations'][current_response_index] = is_correct
    
    # Update timestamp
    annotations[current_question_index]['timestamp'] = datetime.now().isoformat()
    
    # Save annotations back to file
    with open(annotations_filepath, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)
    
    # Update response index in session
    session['current_response_index'] = current_response_index + 1
    
    # Check if we've completed all responses for the current question
    total_responses = len(current_question['responses'])
    if current_response_index + 1 >= total_responses:
        # Move to next question
        session['current_question_index'] = current_question_index + 1
        session['current_response_index'] = 0
    
    return jsonify({"success": True, "next_response_index": current_response_index + 1})

@app.route('/complete')
def complete():
    if 'session_id' not in session:
        return redirect(url_for('index'))
    
    session_id = session.get('session_id')
    annotation_file = f"{session_id}_annotations.json"
    
    return render_template('complete.html', filename=annotation_file)

@app.route('/download/<filename>')
def download(filename):
    filepath = os.path.join(app.config['ANNOTATION_FOLDER'], filename)
    if not os.path.exists(filepath):
        return "File does not exist", 404
    
    return send_file(filepath, as_attachment=True)

@app.route('/nav/<direction>')
def navigate(direction):
    if 'session_id' not in session:
        return redirect(url_for('index'))
    
    current_question_index = session.get('current_question_index', 0)
    current_response_index = session.get('current_response_index', 0)
    total_questions = session.get('total_questions', 0)
    
    session_id = session['session_id']
    data_filepath = os.path.join(app.config['DATA_FOLDER'], f"{session_id}_data.json")
    
    with open(data_filepath, 'r', encoding='utf-8') as f:
        all_data = json.load(f)
    
    if direction == 'prev':
        # If we're at the first response of a question and not the first question
        if current_response_index == 0 and current_question_index > 0:
            # Go to the last response of the previous question
            session['current_question_index'] = current_question_index - 1
            prev_question = all_data[current_question_index - 1]
            session['current_response_index'] = len(prev_question['responses']) - 1
        # If we're not at the first response of the current question
        elif current_response_index > 0:
            # Go to the previous response
            session['current_response_index'] = current_response_index - 1
    elif direction == 'next':
        current_question = all_data[current_question_index]
        total_responses = len(current_question['responses'])
        
        # If we're at the last response of a question and not the last question
        if current_response_index >= total_responses - 1 and current_question_index < total_questions - 1:
            # Go to the first response of the next question
            session['current_question_index'] = current_question_index + 1
            session['current_response_index'] = 0
        # If we're not at the last response of the current question
        elif current_response_index < total_responses - 1:
            # Go to the next response
            session['current_response_index'] = current_response_index + 1
    
    return redirect(url_for('annotate'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)