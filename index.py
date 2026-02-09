from flask import Flask, request, render_template, redirect, url_for, jsonify, send_file, send_from_directory
import os
import pandoc
import libre
import ffmpeg
from flask_cors import CORS
import shutil
from threading import Timer
import json
import uuid
from zip_creator import create_zip_file, cleanup_convert_folder

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global variables to store multiple files and their info
uploaded_files = {}  # {session_id: [{'filename': str, 'filepath': str, 'original_name': str}]}
global_filetest = None
folder_path_1 = 'uploads'
folder_path_2 = 'convert'

with open('static/data/formats.json', 'r') as f:
    data = json.load(f)

pandoc_formats = data['pandocGruppe']
libreoffice_formats = data['tabelleGruppe'] + data['persentGruppe']
ffmpeg_formats = data['videoGruppe'] + data['audioGruppe'] + data['imageGruppe']

def delete_files_in_folder(folder_path):
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Error deleting {file_path}. Reason: {e}')
    else:
        print(f'Folder {folder_path} does not exist')

def convert_file(filepath, target_format):
    """Convert a single file based on its target format"""
    bitrate = "128k"
    try:
        if target_format in libreoffice_formats:
            print(f"Converting with Libreoffice: {filepath}")
            libre.start(filepath, target_format)
        elif target_format in pandoc_formats:
            print(f"Converting with Pandoc: {filepath}")
            pandoc.start(filepath, target_format)
        elif target_format in ffmpeg_formats:
            print(f"Converting with Ffmpeg: {filepath}")
            ffmpeg.start(filepath, target_format, bitrate)
        return True
    except Exception as e:
        print(f"Error converting {filepath}: {e}")
        return False

def convert_multiple_files(file_list, target_format):
    """Convert multiple files sequentially"""
    converted_count = 0
    for file_info in file_list:
        filepath = file_info['filepath']
        if convert_file(filepath, target_format):
            converted_count += 1
        else:
            print(f"Failed to convert: {filepath}")
    return converted_count

def download_file(original_filename, global_filetest):    
    # Use the original filename without the UUID prefix
    if original_filename.count('_') >= 4:  # UUID format: uuid_originalname
        clean_filename = '_'.join(original_filename.split('_')[1:])
    else:
        clean_filename = original_filename
    
    filename = os.path.splitext(clean_filename)[0]
    filethepath = f'convert/{filename}.{global_filetest}'
    try:
        print(f"Ready for download: {filethepath}")
        return send_file(filethepath, as_attachment=True)
    except Exception as e:
        return str(e)

def delete_files_after_delay():
    delete_files_in_folder(folder_path_1)
    delete_files_in_folder(folder_path_2)

@app.route('/', methods=['GET', 'POST'])
def index():
    global global_filetest, uploaded_files
    
    if request.method == 'POST':
        session_id = request.form.get('session_id', str(uuid.uuid4()))
        
        if 'files' in request.files:
            # Multiple file upload
            files = request.files.getlist('files')
            if not files or all(f.filename == '' for f in files):
                return redirect(url_for('index', status='No files selected'))
            
            if global_filetest is None:
                return redirect(url_for('index', status='Please select target format first'))
            
            # Initialize session if not exists
            if session_id not in uploaded_files:
                uploaded_files[session_id] = []
            
            # Save all files
            for file in files:
                if file and file.filename != '':
                    # Create unique filename to avoid conflicts
                    unique_filename = f"{uuid.uuid4()}_{file.filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(filepath)
                    
                    uploaded_files[session_id].append({
                        'filename': unique_filename,
                        'filepath': filepath,
                        'original_name': file.filename
                    })
            
            # Convert all files
            file_count = len(uploaded_files[session_id])
            converted_count = convert_multiple_files(uploaded_files[session_id], global_filetest)
            
            if file_count > 1:
                # Create ZIP file for multiple files
                zip_path = create_zip_file('convert')
                if zip_path:
                    response = redirect(url_for('download_zip', session_id=session_id))
                else:
                    response = redirect(url_for('index', status='Error creating ZIP file'))
            else:
                # Single file - direct download
                file_info = uploaded_files[session_id][0]
                response = redirect(url_for('download', filename=file_info['filename']))  # Use the unique filename
            
            # Clean up after delay
            Timer(10, delete_files_after_delay).start()
            
            # Clear session files
            if session_id in uploaded_files:
                del uploaded_files[session_id]
            
            return response
        
        elif 'file' in request.files:
            # Single file upload (legacy support)
            file = request.files['file']
            
            if file.filename == '':
                return redirect(url_for('index', status='No file selected'))
            
            if file and global_filetest is not None:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                
                if convert_file(filepath, global_filetest):
                    response = redirect(url_for('download', filename=file.filename))
                    Timer(5, delete_files_after_delay).start()
                    return response
                else:
                    return redirect(url_for('index', status='Conversion failed'))
            elif file:
                return redirect(url_for('index', status='File uploaded, but file type not selected'))

    return render_template('index.html', status=request.args.get('status'))

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    global global_filetest
    return download_file(filename, global_filetest)

@app.route('/download_zip/<session_id>', methods=['GET'])
def download_zip(session_id):
    zip_path = os.path.join('convert', 'converted_files.zip')
    try:
        return send_file(zip_path, as_attachment=True, download_name='converted_files.zip')
    except Exception as e:
        return str(e)

@app.route('/empfange_daten', methods=['POST'])
def empfange_daten():
    global global_filetest
    daten = request.json['daten']
    global_filetest = daten
    print(f"Received data: {daten}")
    return jsonify({"status": "successfully received", "message": "Please upload files now"})

@app.route('/get_uploaded_files/<session_id>', methods=['GET'])
def get_uploaded_files(session_id):
    if session_id in uploaded_files:
        return jsonify({
            'files': [{'original_name': f['original_name'], 'filename': f['filename']} 
                     for f in uploaded_files[session_id]]
        })
    return jsonify({'files': []})

@app.route('/remove_file', methods=['POST'])
def remove_file():
    global uploaded_files
    session_id = request.json.get('session_id')
    filename = request.json.get('filename')
    
    if session_id in uploaded_files:
        # Find and remove the file
        uploaded_files[session_id] = [
            f for f in uploaded_files[session_id] 
            if f['filename'] != filename
        ]
        
        # Delete physical file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            try:
                os.unlink(filepath)
            except Exception as e:
                print(f"Error deleting file: {e}")
        
        # Clean up empty session
        if not uploaded_files[session_id]:
            del uploaded_files[session_id]
    
    return jsonify({"status": "success"})

@app.route('/docs')
def doc():
    return render_template("docs.html")

@app.route("/static/data/formats.json")
def get_gruppen():
    return send_from_directory("static/data", "formats.json")

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")