import os
import time
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


# Encrypt and decrypt message functions with timing
def encrypt_message(message, key):
    start_time = time.time()  # Start the timer
    fernet = Fernet(key)
    encrypted = fernet.encrypt(message.encode())
    end_time = time.time()  # End the timer
    encryption_time = (end_time - start_time) * 1000  # Convert to milliseconds
    return encrypted, encryption_time

def decrypt_message(encrypted_message, key):
    start_time = time.time()  # Start the timer
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted_message)
    end_time = time.time()  # End the timer
    decryption_time = (end_time - start_time) * 1000  # Convert to milliseconds
    return decrypted.decode(), decryption_time

# Encrypt and decrypt file functions with timing
def encrypt_file(file_path, key):
    start_time = time.time()  # Start the timer
    fernet = Fernet(key)
    with open(file_path, 'rb') as file:
        original = file.read()
    encrypted = fernet.encrypt(original)
    enc_file_path = os.path.join(ENCRYPTED_FOLDER, os.path.basename(file_path) + '.enc')
    with open(enc_file_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)
    end_time = time.time()  # End the timer
    file_encryption_time = (end_time - start_time) * 1000  # Convert to milliseconds
    return enc_file_path, file_encryption_time

def decrypt_file(file_path, key):
    start_time = time.time()  # Start the timer
    fernet = Fernet(key)
    with open(file_path, 'rb') as encrypted_file:
        encrypted = encrypted_file.read()
    decrypted = fernet.decrypt(encrypted)
    
    original_filename = os.path.basename(file_path).replace('.enc', '')
    dec_file_path = os.path.join(TO_ENCRYPT_FOLDER, original_filename)
    with open(dec_file_path, 'wb') as decrypted_file:
        decrypted_file.write(decrypted)
    end_time = time.time()  # End the timer
    file_decryption_time = (end_time - start_time) * 1000  # Convert to milliseconds
    return dec_file_path, file_decryption_time

# Routes and views
@app.route('/')
def index():
    return render_template('chatroom.html')

@app.route('/encrypt_message', methods=['POST'])
def handle_encrypt_message():
    message = request.form['message']
    key = load_key()
    encrypted_message, encryption_time = encrypt_message(message, key)
    encrypted_message_str = encrypted_message.decode('utf-8')
    return render_template('chatroom.html', encrypted_message=encrypted_message_str, encryption_time=encryption_time)

@app.route('/decrypt_message', methods=['POST'])
def handle_decrypt_message():
    encrypted_message = request.form['encrypted_message'].encode('utf-8')
    key = load_key()
    try:
        decrypted_message, decryption_time = decrypt_message(encrypted_message, key)
        return render_template('chatroom.html', decrypted_message=decrypted_message, decryption_time=decryption_time)
    except Exception as e:
        return render_template('chatroom.html', error=f"Decryption failed: {str(e)}")

@app.route('/encrypt_file', methods=['POST'])
def handle_encrypt_file():
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(TO_ENCRYPT_FOLDER, filename)
    file.save(file_path)
    key = load_key()
    enc_file_path, file_encryption_time = encrypt_file(file_path, key)

    # Generate a file download link
    file_url = url_for('static', filename=f"files/to_encrypt/{os.path.basename(enc_file_path)}")

    # Render the template with encryption time and file link
    return render_template(
        'chatroom.html',
        message="File Encrypted!",
        file_link=file_url,
        file_type='other',
        file_name=os.path.basename(enc_file_path),
        file_encryption_time=file_encryption_time
    )
@app.route('/decrypt_file', methods=['POST'])
def handle_decrypt_file():
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(TO_ENCRYPT_FOLDER, filename)
    file.save(file_path)
    
    key = load_key()
    dec_file_path, file_decryption_time = decrypt_file(file_path, key)

    file_extension = os.path.splitext(dec_file_path)[1].lower()
    file_url = url_for('static', filename=f"files/to_encrypt/{os.path.basename(dec_file_path)}")
    
    if file_extension in ['.png', '.jpg', '.jpeg', '.gif']:
        file_type = 'image'
    elif file_extension in ['.txt', '.csv', '.log', '.pdf']:
        file_type = 'text'
    elif file_extension in ['.mp4', '.avi', '.mov']:
        file_type = 'video'
    else:
        file_type = 'other'

    return render_template(
        'chatroom.html',
        message="File Decrypted!",
        file_link=file_url,
        file_type=file_type,
        file_name=os.path.basename(dec_file_path),
        file_decryption_time=file_decryption_time
    )

if __name__ == '__main__':
    if not os.path.exists('key.key'):
        generate_key()
    app.run(debug=True)
