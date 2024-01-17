import sys
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from base64 import urlsafe_b64encode, urlsafe_b64decode
import bcrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.fernet import Fernet

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.key = None  # Placeholder for the key
        self.checkbox_preference = False

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.username_label = QLabel('Username:')
        self.username_edit = QLineEdit(self)

        self.password_label = QLabel('Password:')
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.save_checkbox = QCheckBox("Save User Choice", self)
        self.save_checkbox.stateChanged.connect(self.save_checkbox_state)
        self.save_checkbox.setEnabled(False)

        self.login_button = QPushButton('Login', self)
        self.register_button = QPushButton('Register', self)

        self.login_button.clicked.connect(self.login)
        self.register_button.clicked.connect(self.register)

        layout.addWidget(self.username_label)
        layout.addWidget(self.username_edit)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.save_checkbox)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)

        self.setLayout(layout)
        self.setWindowTitle('Login Window')

    def load_users(self):
        try:
            with open('users.json', 'rb') as file:
                user_data = file.read()

            # Deserialize the user data and extract the key and encrypted data
            user_info = json.loads(user_data)
            self.key = urlsafe_b64decode(user_info['key'])
            encrypted_data = urlsafe_b64decode(user_info['data'])

            # Decrypt the data using the key
            decrypted_data = self.decrypt_data(encrypted_data)
            users = json.loads(decrypted_data)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            users = {}
            self.key = Fernet.generate_key()  # Generate a new key if not found
        return users

    def save_users(self, users):
        # Serialize the key and encrypted data and save it to the file
        user_info = {
            'key': urlsafe_b64encode(self.key).decode(),
            'data': urlsafe_b64encode(self.encrypt_data(json.dumps(users))).decode()
        }
        with open('users.json', 'w') as file:
            json.dump(user_info, file, indent=2)

    def register_user(self, username, password, users):
        if username in users:
            print("Username already exists. Please choose a different username.")
        else:
            # Hash the password before storing it
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            users[username] = {'password': hashed_password.decode('utf-8')}
            self.save_users(users)
            print("User registered successfully.")

    def login_user(self, username, password, users):
        if username in users:
            # Verify the hashed password
            hashed_password = users[username]['password'].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                print("Login successful. Welcome, {}!".format(username))
                
                # Update checkbox state based on the saved preference
                self.save_checkbox.setChecked(users.get('checkbox_preference', False))
                self.save_checkbox.setEnabled(True)
                return True
        print("Invalid username or password.")
        return False

    def encrypt_data(self, data):
        # Use AES-GCM for encryption
        algorithm = algorithms.AES(self.key[:32])  # Use the first 32 bytes of the key
        cipher = Cipher(algorithm, modes.GCM(b'\x00' * 16))
        encryptor = cipher.encryptor()
        
        # Encrypt the data and get the associated tag
        ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
        tag = encryptor.tag
        
        # Combine ciphertext and tag for storage
        encrypted_data = tag + ciphertext
        return encrypted_data

    def decrypt_data(self, data):
        # Use AES-GCM for decryption
        algorithm = algorithms.AES(self.key[:32])  # Use the first 32 bytes of the key
        cipher = Cipher(algorithm, modes.GCM(b'\x00' * 16, data[:16]))
        decryptor = cipher.decryptor()
        
        # Decrypt the data
        decrypted_data = decryptor.update(data[16:]) + decryptor.finalize()
        return decrypted_data.decode()

    def save_checkbox_state(self, state):
        if self.save_checkbox.isEnabled():
            self.checkbox_preference = state == 2  # 2 corresponds to checked state
            
            # Load users and update checkbox state in users.json
            users = self.load_users()
            users['checkbox_preference'] = self.checkbox_preference
            print(f"Preference changed!")
            self.save_users(users)
        else:
            return

    def login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()

        # Load users and key
        users = self.load_users()

        # Update checkbox state during login
        self.login_user(username, password, users)

    def register(self):
        username = self.username_edit.text()
        password = self.password_edit.text()

        # Load users and key
        users = self.load_users()

        self.register_user(username, password, users)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
