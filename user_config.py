import sys
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from base64 import urlsafe_b64encode, urlsafe_b64decode
import bcrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.fernet import Fernet

import main_window

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.key = None  # Placeholder for the key

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.username_label = QLabel('Username:')
        self.username_edit = QLineEdit(self)

        self.password_label = QLabel('Password:')
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton('Login', self)
        self.register_button = QPushButton('Register', self)

        self.login_button.clicked.connect(self.login)
        self.register_button.clicked.connect(self.register)

        layout.addWidget(self.username_label)
        layout.addWidget(self.username_edit)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)

        self.setLayout(layout)
        self.setWindowTitle('Login Window')

    def load_users(self):
        try:
            with open('user.json', 'rb') as file:
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
        with open('user.json', 'w') as file:
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
                self.run_program()
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

    def save_checkbox_state(self, sender, state):
        # Load users and update checkbox state in users.json
        users = self.load_users()
        users[sender] = state
        
        print(f"{sender} Preference changed!")
        self.save_users(users)

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

    def run_program(self):
        self.close()
        self.main = main_window.MainWindow()
        self.main.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
