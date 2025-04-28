import logging
import socket
from kerberos.msg import *
import kerberos.base.protocol as protocol
from cryptography.fernet import Fernet
import random 

logger = logging.getLogger(__name__)
class client_kerberos_socket:
    KERBEROS_AS_ADDRESS = ('127.0.0.1', 22356)
    KERBEROS_TGS_ADDRESS = ('127.0.0.1', 22223)
    exists = None

    def __new__(cls, *args):
        if client_kerberos_socket.exists is None:
            return super().__new__(cls)
        return client_kerberos_socket.exists
    
    def __init__(self, client = None, password = None, kerberos_as = None):
        if client_kerberos_socket.exists is None:
            self.s = None
            self.session_keys = {} # (ip,port):[key, id]
            self.tgt = None 
            self.ktgs = None # key for tgs 
            self.kcas = client_kerberos_socket.hash_pass(password) # key for as and client
            self.kerberos_as = kerberos_as # maybe add as arg
            self.kerberos_tgs = None # maybe add as arg
            self.client = client
            self.current_connection = None
            self.id_min,self.id_max = 0, 100000
            client_kerberos_socket.exists = self
        else:
            self = client_kerberos_socket.exists

    

    def connect(self, target):
        logger.info(f'connecting to {target}')
        if target not in self.session_keys.keys():
            logger.info(f'target wasnt in session_keys')
            if self.tgt is None:
                if not self.get_tgt():
                    print('could not send failed to get tgt')
                    logger.error('failed to get tgt')
                    return False
            temp_ticket = self.get_service_ticket(target)    
            if temp_ticket is None:
                print('could not get ticket to service')
                logger.error('failed to get service ticket')
                return False
            if not self.setup_temp_id(target, temp_ticket):
                print('failed to close on an id')
                logger.error('failed to close on an id')
                return False
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(target)
        self.current_connection = target
        logger.info(f'connected to {target}')



    def send(self, msg):
        if self.s is None:
            print('cant send if not connected')
        logger.info(f'sending to {self.current_connection} {msg}')
        target = self.current_connection
        msg_to_send = kerberos_wrap(self.session_keys[target][1], msg, self.session_keys[target][0])
        protocol.send(self.s, msg_to_send)



    def recv(self): # used only after a send when there is an open socket with connection .. used for synced comm
        logger.info(f'recv in kerb socket')
        if self.s is None:
            print('recv without a connection')
            logger.error('recv without connection')
            return None
        kerb_wrap:kerberos_wrap = protocol.recv(self.s)
        key = self.get_key_from_id(kerb_wrap.id)
        msg = kerb_wrap.get_msg(key)
        logger.info(f'msg recived : {msg}')
        return msg
    
    def translate_kerb_wrap(self, kerb_wrap):
        return kerb_wrap.get_msg(self.get_key_from_id(kerb_wrap.id))
    
    def close(self):
        self.s.close()
        self.s = None
        self.current_connection = None



    def get_tgt(self):
        logger.info('getting tgt')
        msg = kerberos_msg('AS-REQ', client_name=self.client)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(self.kerberos_as)
        protocol.send(self.s, msg)
        respond = protocol.recv(self.s)
        if respond.request == 'KRB-ERROR':
            print('krb error')
            return False
        if respond.request != "AS-RES":
            print(respond.request + '  smth weird with respond.request')
            return False
        respond.decrypt_msg(self.kcas)
        logger.info(f'decrypted resp: {respond}')
        self.tgt = respond.ticket 
        self.ktgs = respond.session_key
        self.kerberos_tgs = respond.target
        self.s.close()
        self.s = None
        return True
    

    def get_service_ticket(self, target):
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
            return None
        if res.request != "TGS-RES":
            print(res.request + '  smth weird with respond.request')
            return None
        self.session_keys[target] = [res.session_key, None]
        self.s.close()
        self.s = None 
        return res.ticket
    

    def setup_temp_id(self, target, temp_ticket):
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
                return False
            if res.request != "ID-RES":
                print(res.request + '  smth weird with respond.request')
                return False
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
        self.s.close()
        self.s = None 
        return True
    
    def hash_pass(password):
        return b'NLZGwvHzDDMgntjYdR1u4bZ7DhgsUdP5Sph9UCYIJoE='
    
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