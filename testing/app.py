import os
from flask import Flask, render_template, request, send_file, url_for
from cryptography.fernet import Fernet
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Main folder path
MAIN_FOLDER = 'files'

# Subfolder paths inside the main folder
ENCRYPTED_FOLDER = os.path.join(MAIN_FOLDER, 'encrypted')
DECRYPTED_FOLDER = os.path.join(MAIN_FOLDER, 'decrypted')
TO_ENCRYPT_FOLDER = os.path.join('static', 'files', 'to_encrypt')  # Move to static folder

# Set folder paths in the app config
app.config['MAIN_FOLDER'] = MAIN_FOLDER
app.config['ENCRYPTED_FOLDER'] = ENCRYPTED_FOLDER
app.config['DECRYPTED_FOLDER'] = DECRYPTED_FOLDER
app.config['TO_ENCRYPT_FOLDER'] = TO_ENCRYPT_FOLDER

# Ensure that the folders exist
os.makedirs(MAIN_FOLDER, exist_ok=True)
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)
os.makedirs(TO_ENCRYPT_FOLDER, exist_ok=True)

# Load or generate the encryption key
def load_key():
    with open('key.key', 'rb') as key_file:
        return key_file.read()

def generate_key():
    key = Fernet.generate_key()
    with open('key.key', 'wb') as key_file:
        key_file.write(key)

# Encrypt and decrypt message functions
def encrypt_message(message, key):
    fernet = Fernet(key)
    encrypted = fernet.encrypt(message.encode())
    return encrypted

def decrypt_message(encrypted_message, key):
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted_message)
    return decrypted.decode()

# Encrypt and decrypt file functions
def encrypt_file(file_path, key):
    fernet = Fernet(key)
    with open(file_path, 'rb') as file:
        original = file.read()
    encrypted = fernet.encrypt(original)
    enc_file_path = os.path.join(ENCRYPTED_FOLDER, os.path.basename(file_path) + '.enc')
    with open(enc_file_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)
    return enc_file_path

def decrypt_file(file_path, key):
    fernet = Fernet(key)
    with open(file_path, 'rb') as encrypted_file:
        encrypted = encrypted_file.read()
    decrypted = fernet.decrypt(encrypted)
    
    # Save the decrypted file in the TO_ENCRYPT_FOLDER with the original name
    original_filename = os.path.basename(file_path).replace('.enc', '')
    dec_file_path = os.path.join(TO_ENCRYPT_FOLDER, original_filename)
    with open(dec_file_path, 'wb') as decrypted_file:
        decrypted_file.write(decrypted)
    return dec_file_path

# Routes and views
@app.route('/')
def index():
    return render_template('chatroom.html')

@app.route('/encrypt_message', methods=['POST'])
def handle_encrypt_message():
    message = request.form['message']
    key = load_key()
    encrypted_message = encrypt_message(message, key)
    encrypted_message_str = encrypted_message.decode('utf-8')
    return render_template('chatroom.html', encrypted_message=encrypted_message_str)

@app.route('/decrypt_message', methods=['POST'])
def handle_decrypt_message():
    encrypted_message = request.form['encrypted_message'].encode('utf-8')
    key = load_key()
    try:
        decrypted_message = decrypt_message(encrypted_message, key)
        return render_template('chatroom.html', decrypted_message=decrypted_message)
    except Exception as e:
        return render_template('chatroom.html', error=f"Decryption failed: {str(e)}")

@app.route('/encrypt_file', methods=['POST'])
def handle_encrypt_file():
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(TO_ENCRYPT_FOLDER, filename)
    file.save(file_path)
    key = load_key()
    enc_file_path = encrypt_file(file_path, key)
    return send_file(enc_file_path, as_attachment=True)

@app.route('/decrypt_file', methods=['POST'])
def handle_decrypt_file():
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(TO_ENCRYPT_FOLDER, filename)  # Save uploaded file in TO_ENCRYPT_FOLDER
    file.save(file_path)
    
    key = load_key()
    # Remove '.enc' from the file name to save as the original file
    dec_file_path = decrypt_file(file_path, key)

    # Detect file type to display or provide a download link
    file_extension = os.path.splitext(dec_file_path)[1].lower()
    file_url = url_for('static', filename=f"files/to_encrypt/{os.path.basename(dec_file_path)}")
    
    if file_extension in ['.png', '.jpg', '.jpeg', '.gif']:  # Image file
        file_type = 'image'
    elif file_extension in ['.txt', '.csv', '.log', '.pdf']:  # Text and PDF files
        file_type = 'text'
    elif file_extension in ['.mp4', '.avi', '.mov']:  # Video files
        file_type = 'video'
    else:
        file_type = 'other'

    return render_template(
        'chatroom.html',
        message="File Decrypted!",
        file_link=file_url,
        file_type=file_type,
        file_name=os.path.basename(dec_file_path)
    )

if __name__ == '__main__':
    if not os.path.exists('key.key'):
        generate_key()
    app.run(debug=True)
