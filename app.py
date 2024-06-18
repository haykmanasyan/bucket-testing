import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string
from google.cloud import storage
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# Ensure the environment variable is set
if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
    raise RuntimeError("The GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")

# Initialize Google Cloud Storage client
storage_client = storage.Client()
bucket_name = 'xmpl-bkt'
bucket = storage_client.bucket(bucket_name)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    blobs = bucket.list_blobs()
    files = [blob.name for blob in blobs]
    return render_template_string('''
    <!doctype html>
    <title>Upload File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data action="/upload">
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    <h2>Files</h2>
    <ul>
    {% for filename in files %}
      <li><a href="{{ url_for('download_file', filename=filename) }}">{{ filename }}</a></li>
    {% endfor %}
    </ul>
    ''', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        blob = bucket.blob(filename)
        blob.upload_from_file(file)
        return redirect(url_for('index'))
    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    blob = bucket.blob(filename)
    blob.download_to_filename(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=8080, debug=True)
