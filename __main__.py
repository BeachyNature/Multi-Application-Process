import logging.config
import os
import sys
import json
import bcrypt
from base64 import urlsafe_b64encode, urlsafe_b64decode
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.fernet import Fernet

# Local imports
import landing_page

# Insert logging
import yaml
import logging
import logging.config

with open('logging.yaml', 'r') as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)
logger = logging.getLogger(__name__)

def directory_exist(path) -> None:
    """
    Macro: check if directory exist
    """
    if not os.path.exists(path):
        return os.makedirs(path)

class LoginWindow(QWidget):
    """
    Main login window for the user to interact with the tool.
    """

    key = None
    user_path = os.path.expanduser("~")
    folder_path = os.path.join(user_path, "MAPS-Python")
    plot_folder = os.path.join(folder_path, "Saved Plots")
    file_path = os.path.join(folder_path,'user.json')

    def __init__(self) -> None:
        super().__init__()

        self.init_ui()

    def init_ui(self) -> None:
        """
        Setup the login window for the user to sign in/
        """

        self.label = QLabel()
        self.username_label = QLabel('Username:')
        self.username_edit = QLineEdit(self)

        self.password_label = QLabel('Password:')
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton('Login', self)
        self.login_button.clicked.connect(self.login)

        self.register_button = QPushButton('Register', self)        
        self.register_button.clicked.connect(self.register)
        self.register_button.setVisible(False)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_edit)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setWindowTitle('Login Window')
        self.check_user_file()
        return

    def check_user_file(self) -> None:
        """
        Check if user file exist or not
        """
        if os.path.exists(self.file_path):
            self.username_edit.setText(next(iter(self.load_users())))
            self.password_edit.returnPressed.connect(self.login)
            self.password_edit.setFocus()
            return
        
        # If they are a new user
        print("Welcome to MAPS-Python! In order to start, you need to register.")
        self.register_button.setVisible(True)
        return

    def load_users(self) -> dict:
        """
        Read the created user file
        """    
        try:
            with open(self.file_path, 'rb') as file:
                user_data = file.read()

            # Deserialize the user data and extract the key and encrypted data
            user_info = json.loads(user_data)
            self.key = urlsafe_b64decode(user_info['key'])
            encrypted_data = urlsafe_b64decode(user_info['data'])

            # Decrypt the data using the key
            decrypted_data = self.decrypt_data(encrypted_data)
            users = json.loads(decrypted_data)
            return users

        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            self.key = Fernet.generate_key()
            return {}

    def save_users(self, users, _bool) -> None:
        """
        Save the user information when created
        """
            
        user_info = {
            'key': urlsafe_b64encode(self.key).decode(),
            'data': urlsafe_b64encode(self.encrypt_data(json.dumps(users))).decode()
        }

        if _bool: # Check if the user is registering or not
            for path in [self.folder_path, self.plot_folder]:
                path_create = directory_exist(path)
            print(f"Test {path_create}")

        # Update json file
        with open(self.file_path, 'w') as file:
            json.dump(user_info, file, indent=2)
        return
    
    def register_user(self, username, password, users) -> None:
        """
        Create the user account and has their new pass
        """
    
        if username not in users:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            users[username] = {'password': hashed_password.decode('utf-8')}
            self.save_users(users, True)
            self.label.setText("User registered successfully.")
            return
        
        # Let user know that account exist
        self.label.setText("Username already exists.")
        return

    def login_user(self, username, password, users) -> bool:
        """
        Login the user based on the information in the users json
        """
    
        if username in users:
            hashed_password = users[username]['password'].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                print("Login successful. Welcome, {}!".format(username))
                self.run_program()
                return True

        # Highlight the invalid password for user to easily try new attempt
        self.password_edit.selectAll()
        self.label.setText("Invalid username or password.")
        return False

    def encrypt_data(self, data) -> None:
        """
        Encrypt the data that goes into the file
        """
        
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

    def decrypt_data(self, data) -> None:
        """
        Decrypt the data to process the data for login or preferences
        """

        # Use AES-GCM for decryption
        algorithm = algorithms.AES(self.key[:32])  # Use the first 32 bytes of the key
        cipher = Cipher(algorithm, modes.GCM(b'\x00' * 16, data[:16]))
        decryptor = cipher.decryptor()
        
        # Decrypt the data
        decrypted_data = decryptor.update(data[16:]) + decryptor.finalize()

        # TODO: Get type for return
        return decrypted_data.decode()

    def save_checkbox_state(self, sender, state) -> None:
        """
        User preference checkboxes
        """

        # Load users and update checkbox state in users.json
        users = self.load_users()
        users[sender] = state
        
        print(f"{sender} Preference changed!")
        self.save_users(users, False)
        return

    def login(self) -> None:
        """
        User login process data from text fields
        """

        username = self.username_edit.text()
        password = self.password_edit.text()

        # Load users and key
        users = self.load_users()
        self.login_user(username, password, users)
        return

    def register(self) -> None:
        """
        Register the user with the text fields
        """
    
        username = self.username_edit.text()
        password = self.password_edit.text()

        # Load users and key
        users = self.load_users()
        self.register_user(username, password, users)
        return

    def run_program(self) -> None:
        """
        Run the program once the user logs in successfully
        """

        self.main = landing_page.MainWindow()
        self.main.show()
        self.close()
        return
    
    def closeEvent(self, event) -> None:
        """
        Pop-up a confirmation message to ensure user wants to close window
        """
        logger.debug("Closing window!")
        event.ignore() # Test
        #TODO: Ask user if they want to close window
        return
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
