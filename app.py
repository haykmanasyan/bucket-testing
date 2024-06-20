import os
import datetime
from flask import Flask, request, redirect, url_for, render_template_string
from google.cloud import storage
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png'}

# double check application credentials

if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):

    raise RuntimeError("The GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")

# set the bucket as xmpl-bkt
storage_client = storage.Client()
bucket_name = 'xmpl-bkt'
bucket = storage_client.bucket(bucket_name)

# check with allowed extensions
# png for now, will update the file extensions to eventually cover scans

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# html
# list the files in a drop down menu (similar to the scans)
# upload the files with the button
# view the image on the right, with option to download under the hyperlink

@app.route('/')
def index():

    blobs = bucket.list_blobs()
    files = [blob.name for blob in blobs]
    
    return render_template_string('''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Testing</title>
        <style>
            body {
                display: flex;
                flex-direction: row;
                justify-content: space-between;
            }
            .container {
                flex: 1;
            }
            .image-container {
                flex: 1;
                display: flex;
                justify-content: center;
                align-items: center;
                flex-direction: column;
            }
            img {
                max-width: 100%;
                max-height: 500px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Upload new File</h1>
            <form method=post enctype=multipart/form-data action="/upload">
              <input type=file name=file>
              <input type=submit value=Upload>
            </form>
            <h2>Files</h2>
            <select id="fileDropdown" onchange="displayImage(this)">
                <option value="">Select a file</option>
                {% for filename in files %}
                    <option value="{{ filename }}">{{ filename }}</option>
                {% endfor %}
            </select>
            <div>
                <a id="downloadLink" href="#" style="display: none;" download>Download Selected Image</a>
            </div>
        </div>
        <div class="image-container">
            <img id="selectedImage" src="" alt="Selected Image" style="display: none;">
        </div>
        <script>
            function displayImage(select) {
                var filename = select.value;
                if (filename) {
                    var imageUrl = "/view/" + filename;
                    document.getElementById('selectedImage').src = imageUrl;
                    document.getElementById('selectedImage').style.display = 'block';
                    document.getElementById('downloadLink').href = imageUrl;
                    document.getElementById('downloadLink').style.display = 'block';
                } else {
                    document.getElementById('selectedImage').style.display = 'none';
                    document.getElementById('downloadLink').style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    ''', files=files)

# check if the file can be uploaded
# upload the file

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

# view the file
# generate signed url
# valid signed url for one hour

@app.route('/view/<filename>')
def view_file(filename):

    blob = bucket.blob(filename)
    expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    blob_url = blob.generate_signed_url(expiration=expiration_time)
    return redirect(blob_url)

# main
# host on port 8080

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=8080, debug=True)
