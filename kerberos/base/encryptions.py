import logging
import pickle
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)
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
    def decrypt(value, key, was_bytes = False):
        logger.info(f'decrypting value {value}')
        if value is None:
            return None
        print(value)
        
        cipher_suite = Fernet(key)
        data = cipher_suite.decrypt(value)
        logger.info(f'decrypted value {data}')
        if not was_bytes:
            data = pickle.loads(data)
            logger.info(f'unpickled value {data}')

        return data