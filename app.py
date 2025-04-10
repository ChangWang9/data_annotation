# app.py (only showing the core concept of modifications/additions, others remain unchanged)
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
                    # Assuming neg_reasoning_paths is a list containing question/response information
                    # Modify as needed if your actual data structure is different

                    question_text = item.get('question', '(No question)')
                    response_text = item.get('neg_reasoning_paths', '(No response)')[0]
                    
                    question_text = fix_tabular_to_array(question_text)
                    response_text = fix_tabular_to_array(response_text)
                    
                    data.append({
                        'question': question_text,
                        'response': response_text
                    })
            except json.JSONDecodeError:
                continue
    
    if not data:
        os.remove(filepath)
        return "No valid data found. Please check if the file format is correct", 400
    
    data_filepath = os.path.join(app.config['DATA_FOLDER'], f"{session_id}_data.json")
    with open(data_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    annotations_filepath = os.path.join(app.config['ANNOTATION_FOLDER'], f"{session_id}_annotations.json")
    with open(annotations_filepath, 'w', encoding='utf-8') as f:
        json.dump([], f)
    
    session['session_id'] = session_id
    session['current_index'] = 0
    session['total_items'] = len(data)
    
    return redirect(url_for('annotate'))


@app.route('/annotate')
def annotate():
    if 'session_id' not in session:
        return redirect(url_for('index'))
    
    session_id = session['session_id']
    current_index = session.get('current_index', 0)
    total_items = session.get('total_items', 0)
    
    if current_index >= total_items:
        return redirect(url_for('complete'))
    
    data_filepath = os.path.join(app.config['DATA_FOLDER'], f"{session_id}_data.json")
    with open(data_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        current_item = data[current_index]  # Already contains question and response

    # Convert question and response from Markdown to HTML
    # extras can include extensions you want to enable, like 'fenced-code-blocks', 'tables', etc.
    current_item['question_html'] = markdown2.markdown(current_item['question'], extras=["fenced-code-blocks"])
    current_item['response_html'] = markdown2.markdown(current_item['response'], extras=["fenced-code-blocks"])

    return render_template(
        'annotate.html', 
        item=current_item, 
        current=current_index + 1, 
        total=total_items,
        countdown=60
    )
# Other routes (record_annotation, complete, download, navigate) remain unchanged
# ...

@app.route('/record', methods=['POST'])
def record_annotation():
    if 'session_id' not in session:
        return jsonify({"error": "No active session"}), 400
    
    data = request.json
    is_correct = data.get('is_correct')
    
    if is_correct is None:
        return jsonify({"error": "Missing is_correct parameter"}), 400
    
    session_id = session['session_id']
    current_index = session.get('current_index', 0)
    
    # Read current item data from file
    data_filepath = os.path.join(app.config['DATA_FOLDER'], f"{session_id}_data.json")
    with open(data_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        current_item = data[current_index]
    
    # Record annotation
    annotation = {
        "index": current_index,
        "content": current_item,
        "is_correct": is_correct,
        "timestamp": datetime.now().isoformat()
    }
    
    # Read existing annotations from file
    annotations_filepath = os.path.join(app.config['ANNOTATION_FOLDER'], f"{session_id}_annotations.json")
    with open(annotations_filepath, 'r', encoding='utf-8') as f:
        annotations = json.load(f)
    
    # Add new annotation and save back to file
    annotations.append(annotation)
    with open(annotations_filepath, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)
    
    # Update index in session
    session['current_index'] = current_index + 1
    
    return jsonify({"success": True, "next_index": current_index + 1})

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
    
    current_index = session.get('current_index', 0)
    total_items = session.get('total_items', 0)
    
    if direction == 'prev' and current_index > 0:
        session['current_index'] = current_index - 1
    elif direction == 'next' and current_index < total_items - 1:
        session['current_index'] = current_index + 1
    
    return redirect(url_for('annotate'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)