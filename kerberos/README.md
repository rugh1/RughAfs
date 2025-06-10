# Documentation for Python Files in 'kerberos'

This document contains the content of all Python (.py) files found in this directory and its subdirectories.

## __init__.py

python


## base\__init__.py

python
class nothing:
    def __init__(self):
        pass

## base\encryptions.py

python
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

## base\msg.py

python
from .encryptions import encr

class command(encr):
    user = None
    def __init__(self, cmd , data, src = None, ):
        self.sender = command.user #username /type of client idk
        self.src = src # where to write to it 
        self.cmd = cmd # command
        self.data = data # data for command
        
    def encrypt(self, key):
        self.sender = super().encrypt(self.sender, key)
        self.cmd = super().encrypt(self.cmd, key)
        self.data = super().encrypt(self.data, key)
        self.src = super().encrypt(self.src, key)


    def decrypt(self, key):
        self.sender = super().decrypt(self.sender, key)
        self.cmd = super().decrypt(self.cmd, key)
        self.data = super().decrypt(self.data, key)
        self.src = super().decrypt(self.src, key)

        

    def __str__(self):
        return f'cmd: {self.cmd} ,data: {self.data}, sender: {self.sender}, src: {self.src}'

## base\protocol.py

python
import logging
import pickle
from .msg import command

logger = logging.getLogger(__name__)

def int_to_bytes(number: int) -> bytes:
    return number.to_bytes(length=(8 + (number + (number < 0)).bit_length()) // 8, byteorder='big', signed=True)

def int_from_bytes(binary_data: bytes) -> int:
    return int.from_bytes(binary_data, byteorder='big', signed=True)

def int_from_bytes_client(binary_data: bytes) -> int:
    return int.from_bytes(binary_data, byteorder='little', signed=True)

def int_to_bytes_client(number: int) -> bytes:
    return number.to_bytes(length=(8 + (number + (number < 0)).bit_length()) // 8, byteorder='little', signed=True)

def send(connected_socket, msg:object):
    """
    Send a message over the connected socket.

    :param connected_socket: The connected socket to send the message through.
    :type connected_socket: socket.socket

    :param msg: The message to be sent.
    :type msg: str

    :return: None
    :rtype: None
    """
    logger.info(f'sending {msg}')
    print(f'sending: {msg}')
    data = pickle.dumps(msg)
    # Check if the last character of the 'msg' string is a space
    # Convert the length of the 'msg' string to hexadecimal representation, excluding the '0x' prefix
    msg = int_to_bytes(len(data)) + b'!' + data
    print(msg)
    # Encode the modified 'msg' string and send it through the 'connected_socket'
    connected_socket.send(msg)


def recv(connected_socket):
    """
    Receive a message from the connected socket.

    :param connected_socket: The connected socket to receive the message from.
    :type connected_socket: socket.socket

    :return: A list containing the split components of the received message.
    :rtype: list[str]
    """
    # Receive the length of the message in hexadecimal
    print('reciving')
    length_hex = b''
    tmp = b''
    while tmp != b'!':
        print(length_hex)
        length_hex += tmp
        tmp = connected_socket.recv(1)

    # Convert the length to an integer
    length = int_from_bytes(length_hex)

    # Receive the message until the expected length is reached
    received_msg = b''
    while len(received_msg) < length:
        received_msg += connected_socket.recv(1)
    data = pickle.loads(received_msg)
    # Split the received message using '!' as the separator
    logger.info(f'recived {data}')
    return data

def client_recv(connected_socket):
    len = int_from_bytes_client(connected_socket.recv(4)) #size of int 
    print(len)
    data = connected_socket.recv(len - 1) # -1 because of null terminator 
    print(data)
    return data.decode()

def send_client(connected_socket, status:int):
    print(f'sending to client {status}')
    bytes_to_send = int_to_bytes_client(status)
    bytes_to_send = bytes(4-len(bytes_to_send)) + bytes_to_send
    print(f'bytes: {bytes_to_send}')
    connected_socket.send(bytes_to_send)

## client.py

python
import base64
import logging
import socket
from kerberos.msg import *
import kerberos.base.protocol as protocol
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import random 

logger = logging.getLogger(__name__)
class client_kerberos_socket:
    exists = None  # placeholder for the first instance

    def __new__(cls, **args):  # returns the same mem if already allocated
        if client_kerberos_socket.exists is None:
            return super().__new__(cls)
        return client_kerberos_socket.exists

    def __init__(self, client=None, password=None, kerberos_as=None):
        # init function
        if client_kerberos_socket.exists is None:
            self.s = None
            self.session_keys = {}  # (ip, port): [key, id]
            self.tgt = None
            self.ktgs = None  # key for tgs
            self.kcas = client_kerberos_socket.hash_pass(password)  # key for as and client
            print(f'kcas: {self.kcas}')
            self.kerberos_as = kerberos_as  # maybe add as arg
            self.kerberos_tgs = None  # maybe add as arg
            self.client = client
            self.current_connection = None
            self.id_min, self.id_max = 0, 100000
            client_kerberos_socket.exists = self
        else:
            self = client_kerberos_socket.exists

    

    def connect(self, target):
        status = True
        try:
            logger.info(f'connecting to {target}')
            if target not in self.session_keys.keys():
                logger.info(f'target wasnt in session_keys')
                if self.tgt is None:
                    if not self.login(): #idk what im thinking bout it 
                        print('could not send failed to get tgt')
                        logger.error('failed to get tgt')
                        raise Exception('failed to get tgt')
                temp_ticket = self.get_service_ticket(target)    
                if temp_ticket is None:
                    print('could not get ticket to service')
                    logger.error('failed to get service ticket')
                    raise Exception('failed getting ticket to server') 
                if not self.setup_temp_id(target, temp_ticket):
                    print('failed to close on an id')
                    logger.error('failed to close on an id')
                    raise Exception('failed to close on an id')
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect(target)
            self.current_connection = target
        except socket.error as err:
            print(f'encounterd socket err while connecting to {target} : {str(err)}')
            status = False
            self.s = None
            self.current_connection = None
        except Exception as err:
            print(f'encounterd an err: {str(err)}')
            self.s = None
            self.current_connection = None
            status = False
        logger.info(f'connected to {target}')
        return status



    def send(self, msg):
        status = True
        try:
            if self.s is None:
                print('cant send if not connected')
                status = False
                raise Exception('cant send if not connected')
            logger.info(f'sending to {self.current_connection} {msg}')
            target = self.current_connection
            msg_to_send = kerberos_wrap(self.session_keys[target][1], msg, self.session_keys[target][0])
            protocol.send(self.s, msg_to_send)
        except socket.error as err:
            print(f'encounterd err while sending: {err}')
            status = False
        except Exception as err:
            print(f'encounterd exception while sending : {str(err)}')
            status = False
        finally:
            return status



    def recv(self): # used only after a send when there is an open socket with connection .. used for synced comm
        try:
            logger.info(f'recv in kerb socket')
            if self.s is None:
                print('cant send if not connected')
                status = None
                raise Exception('cant send if not connected')
            kerb_wrap:kerberos_wrap = protocol.recv(self.s)
            key = self.get_key_from_id(kerb_wrap.id)
            msg = kerb_wrap.get_msg(key)
            logger.info(f'msg recived : {msg}')
            status = msg
        except socket.error as err:
            print(f'encounterd err while sending: {err}')
            status = None
        except Exception as err:
            print(f'encounterd exception while sending : {str(err)}')
            status = None
        finally: 
            return status
 
    def translate_kerb_wrap(self, kerb_wrap):
        return kerb_wrap.get_msg(self.get_key_from_id(kerb_wrap.id))
    

    def close(self):
        if self.s == None: 
            self.current_connection = None
            return
        self.s.close()
        self.s = None
        self.current_connection = None

    def login(self):
        status = True
        try:
            logger.info('logging in')
            msg = kerberos_msg('AS-REQ', client_name=self.client)
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect(self.kerberos_as)
            protocol.send(self.s, msg)
            respond = protocol.recv(self.s)
            if respond.request == 'KRB-ERROR':
                print('krb error')
                status = False
                raise Exception('recived krb error')
            if respond.request != "AS-RES":
                print(respond.request + '  smth weird with respond.request')
                status = False
                raise Exception(f'didnt get as-res got {respond.request}')
            respond.decrypt_msg(self.kcas)
            logger.info(f'decrypted resp: {respond}')
            msg = kerberos_msg('AS-REQ', client_id=respond.client + 1)
            protocol.send(self.s, msg)
            respond = protocol.recv(self.s)
            respond.decrypt_msg(self.kcas)
            print(respond)
            if respond.request == 'KRB-ERROR':
                print('krb error')
                status = False
                raise Exception('recived krb error')
            if respond.request != "AS-RES":
                print(respond.request + '  smth weird with respond.request')
                status = False
                raise Exception(f'didnt get as-res got {respond.request}')
            self.tgt = respond.ticket 
            self.ktgs = respond.session_key
            self.kerberos_tgs = respond.target

        except socket.error as err:
            print('socket err encounterd while getting tgt :', err)
            status = False
        except Exception as err:
            print('unknown error encounterd while getting tgt:', err)
            status = False
        finally:
            self.s.close()
            self.s = None
            return status

    def get_service_ticket(self, target):
        resp_status = None
        try:
            msg = kerberos_msg('TGS-REQ', self.client, target=target, ticket=self.tgt)
            logger.info(f'getting service ticket with msg: {msg}')
            msg.encrypt_msg(self.ktgs)
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect(self.kerberos_tgs)
            protocol.send(self.s, msg)
            res = protocol.recv(self.s)
            res.decrypt_msg(self.ktgs)
            logger.info(f'recived {res}')
            if res.request == 'KRB-ERROR':
                print('krb error')
                raise Exception('recived krb error')
            if res.request != "TGS-RES":
                print(res.request + '  smth weird with respond.request')
                raise Exception(f'response expected to be TGS-RES instead recived: {msg.request}')
            self.session_keys[target] = [res.session_key, None]
            resp_status = res.ticket
        except socket.error as err:
            print('socket err encounterd while getting service ticket:', err)
        except Exception as err:
            print('unknown error encounterd while service ticket:', err)
        finally:
            self.s.close()
            self.s = None
            return resp_status

    def setup_temp_id(self, target, temp_ticket):
        status = True
        try:    
            logger.info(f'setting up id with {target}')
            target_key = self.session_keys[target][0]
            id = self.get_rand_id()
            msg = kerberos_msg('ID-REQ', client_name=self.client, client_id=id, ticket=temp_ticket)
            logger.info(f'msg before enc {msg}')
            msg.encrypt_id(target_key)

            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect(target)
            protocol.send(self.s, msg)

            res = protocol.recv(self.s)
            res.decrypt_id(target_key)

            while res.request != 'ID-CONFIRM':
                if res.request == 'KRB-ERROR':
                    print('krb error')
                    raise Exception('recived KRB-ERROR')
                if res.request != "ID-RES":
                    print(res.request + '  smth weird with respond.request')
                    raise Exception('encounterd a diffrent response (not ID-RES)')
                if not self.check_id_in_dict(res.client_id):
                    id = res.client_id
                    msg = kerberos_msg('ID-REQ', self.client, client_id=id, ticket=temp_ticket)
                    msg.encrypt_id(target_key)
                    protocol.send(self.s, msg)
                else: 
                    id = self.get_rand_id()
                    msg = kerberos_msg('ID-REQ', self.client, client_id=id, ticket=temp_ticket)
                    msg.encrypt_id(target_key)
                    protocol.send(self.s, msg)

                res = protocol.recv(self.s)
                res.decrypt_id(target_key)
                
            logger.info(f'closed on id: {id}')
            self.session_keys[target][1] = id

        except socket.error as err:
            print(f'encounterd socket err : {str(err)}')
            status = False
        except Exception as err:
            print(f'encounterd error : {str(err)}')
            status = False
        finally:
            self.s.close()
            self.s = None 
            return status
    
    def hash_pass(password):
        return client_kerberos_socket.derive_key(password.encode())
    
    def derive_key(password: bytes, salt: bytes = b'\xa1{V\x04\xd9\xc3\x08\xc8\xc2\xc0\x80\x06:\xccu\xfc', iterations: int = 100_000) -> bytes:
        kdf = PBKDF2HMAC( algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations,)
        return base64.urlsafe_b64encode(kdf.derive(password))

    def get_rand_id(self):
        rand = random.randint(self.id_min,self.id_max)
        while self.check_id_in_dict(rand):
            rand = random.randint(self.id_min,self.id_max)
        return rand
    
    def check_id_in_dict(self, id):
        for i in self.session_keys.values():
            if i[1] == id:
                return True
        return False
    
    def get_key_from_id(self, id):
        for i in self.session_keys.values():
            if i[1] == id:
                return i[0]
        return None
    
    def __str__(self):
        return f"""
                s: {self.s}
                session_keys: {self.session_keys}
                tgt: {self.tgt}
                ktgs: {self.ktgs}
                kcas: {self.kcas}
                kerberos_as: {self.kerberos_as}
                kerberos_tgs: {self.kerberos_tgs}
                client: {self.client}
                current_connection: {self.current_connection}
                id_min: {self.id_min}, id_max: {self.id_max}
                """

## msg.py

python
import pickle
from kerberos.base.encryptions import encr
        

class kerberos_msg(encr):
    def __init__(self, request, client_name = None, client_id = None ,target = None, session_key = None, ticket = None):
        self.request = request
        self.client = client_name
        self.client_id = client_id
        self.target = target
        self.session_key = session_key
        self.ticket = ticket
    
    def encrypt_msg(self, key):
        print(f'encrypting msg: {self}')
        self.client = super().encrypt(self.client, key)
        self.target = super().encrypt(self.target, key)
        self.session_key = super().encrypt(self.session_key, key)

    def encrypt_id(self, key):
        print(f'encrypting id: {self}')
        self.client = super().encrypt(self.client, key)
        self.target = super().encrypt(self.target, key)
        self.session_key = super().encrypt(self.session_key, key)
        self.client_id = super().encrypt(self.client_id, key)

    def decrypt_msg(self, key):
        print(f'decrypting msg: {self}')
        self.client = super().decrypt(self.client, key)
        self.target = super().decrypt(self.target, key)
        self.session_key = super().decrypt(self.session_key, key, True)
        
    def decrypt_id(self, key):
        print(f'decrypting id: {self}')
        self.client = super().decrypt(self.client, key)
        self.target = super().decrypt(self.target, key)
        self.session_key = super().decrypt(self.session_key, key, True)
        self.client_id = super().decrypt(self.client_id, key)

    # def decrypt(self, key):
    #     if type(self.client_id) is bytes:
    #         self.decrypt_id(key)
    #     else:
    #         self.decrypt_msg(key)
    
    def __str__(self):
        return f"""
                request: {self.request}
                client: {self.client}
                client_id: {self.client_id}
                target: {self.target}
                session_key: {self.session_key}
                ticket: {self.ticket}
                """


class kerberos_wrap(encr):
    def __init__(self, id, msg, key):
        self.id = id 
        self.msg = self.encrypt(msg, key)

    def get_msg(self, key):
        return encr.decrypt(self.msg, key)
    
    def __str__(self):
        return f'id: {self.id}, {self.msg}'
    
class ticket(encr):
    def __init__(self, key, client):
        self.key = key
        self.client = client
    
    def encrypt(self, key):
        self.key = super().encrypt(self.key, key)
        self.client = super().encrypt(self.client, key)

    def decrypt(self, key):
        self.key = super().decrypt(self.key, key, True)
        self.client = super().decrypt(self.client, key)

    def __str__(self):
        return f"""
                key: {self.key}
                client: {self.client}
                """

