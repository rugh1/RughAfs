import pickle
from cryptography.fernet import Fernet

class encr:
    @staticmethod
    def encrypt(value, key):
        if value is None:
            return None 
        if type(value) != bytes:
            value = pickle.dumps(value)
        cipher_suite = Fernet(key)
        return cipher_suite.encrypt(value)
        #idea encrpyt user name but give in ticket /first iteraction random number that represents the user
    
    @staticmethod
    def decrypt(value, key):
        if value is None:
            return None
        cipher_suite = Fernet(key)
        return cipher_suite.decrypt(value)