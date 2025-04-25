import socket
from kerberos.msg import *
import kerberos.base.protocol as protocol
from cryptography.fernet import Fernet
import random 

class client_kerberos_socket:
    KERBEROS_AS_ADDRESS = ('127.0.0.1', 22356)
    KERBEROS_TGS_ADDRESS = ('127.0.0.1', 22223)
    exists = None

    def __new__(cls, *args):
        if client_kerberos_socket.exists is None:
            return super().__new__(cls)
        return client_kerberos_socket.exists
    
    def __init__(self, client = None, password = None):
        if client_kerberos_socket.exists is None:
            self.s = None
            self.seasion_keys = {} # (ip,port):[key, id]
            self.tgt = None 
            self.ktgs = None # key for tgs 
            self.kcas = client_kerberos_socket.hash_pass(password) # key for as and client
            self.kerberos_as = self.KERBEROS_AS_ADDRESS # maybe add as arg
            self.kerberos_tgs = self.KERBEROS_TGS_ADDRESS # maybe add as arg
            self.client = client
            self.current_connection = None
            self.id_min,self.id_max = 0, 100000
            client_kerberos_socket.exists = self
        else:
            self = client_kerberos_socket.exists

    

    def connect(self, target):
        if target not in self.seasion_keys.keys():
            if self.tgt is None:
                if not self.get_tgt():
                    print('could not send failed to get tgt')
                    return False
            temp_ticket = self.get_service_ticket(target)    
            if temp_ticket is None:
                print('could not get ticket to service')
                return False
            if not self.setup_temp_id(target, temp_ticket):
                print('failed to close on an id')
                return False
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(target)
        self.current_connection = target



    def send(self, msg):
        if self.s is None:
            print('cant send if not connected')
        target = self.current_connection
        msg_to_send = kereboros_wrap(self.seasion_keys[target][1], msg, self.seasion_keys[target][0])
        protocol.send(self, msg_to_send)



    def recv(self): # used only after a send when there is an open socket with connection .. used for synced comm
        if self.s is None:
            print('recv without a connection')
            return None
        kerb_wrap = protocol.recv(self.s)
        key = self.get_key_from_id(kerb_wrap.id)
        original_data = encr.decrypt(kerb_wrap.msg, key)
        return pickle.loads(original_data)
        
    
    def close(self):
        self.s.close()
        self.s = None
        self.current_connection = None



    def get_tgt(self):
        msg = kerberos_msg('AS-REQ', self.client)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(self.kerberos_as)
        protocol.send(self, msg)
        respond = protocol.recv()
        if respond.request == 'KRB-ERROR':
            print('krb error')
            return False
        if respond.request != "AS-RES":
            print(respond.request + '  smth weird with respond.request')
            return False
        respond.decrypt(self.kcas)
        self.tgt = respond.ticket 
        self.ktgs = respond.session_key
        self.s.close()
        self.s = None
        return True
    

    def get_service_ticket(self, target):
        msg = kerberos_msg('TGS-REQ', self.client, target=target, ticket=self.tgt)
        msg.encrypt_msg(self.ktgs)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(self.kerberos_tgs)
        protocol.send(self.s, msg)
        res = protocol.recv(self.s)
        res.decrpyt(self.ktgs)
        if res.request == 'KRB-ERROR':
            print('krb error')
            return None
        if res.request != "TGS-RES":
            print(res.request + '  smth weird with respond.request')
            return None
        self.seasion_keys[target] = [res.seasion_key, None]
        self.s.close()
        self.s = None 
        return res.ticket
    

    def setup_temp_id(self, target, temp_ticket):
        target_key = self.seasion_keys[target][0]
        id = self.get_rand_id()
        msg = kerberos_msg('ID-REQ', client_name=self.client, client_id=id, ticket=temp_ticket)
        msg.encrypt_id(target_key)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(self.kerberos_tgs)
        protocol.send(self.s, msg)

        res = protocol.recv(self.s)
        res.decrpyt(target_key)

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
                protocol.send(msg)
            else: 
                id = self.get_rand_id()
                msg = kerberos_msg('ID-REQ', self.client, client_id=id, ticket=temp_ticket)
                msg.encrypt_id(target_key)
                protocol.send(msg)

            res = protocol.recv(self.s)
            res.decrpyt(target_key)

        self.seasion_keys[target][1] = id
        self.s.close()
        self.s = None 
        return True
    
    def hash_pass(password):
        return password
    
    def get_rand_id(self):
        rand = random.randint(self.id_min,self.id_max)
        while self.check_id_in_dict(rand):
            rand = random.randint(self.id_min,self.id_max)
        return rand
    
    def check_id_in_dict(self, id):
        for i in self.seasion_keys.values():
            if i[1] == id:
                return True
        return False
    
    def get_key_from_id(self, id):
        for i in self.seasion_keys.values():
            if i[1] == id:
                return i[0]
        return None
    
    def __str__(self):
        return f"""
                s: {self.s}
                seasion_keys: {self.seasion_keys}
                tgt: {self.tgt}
                ktgs: {self.ktgs}
                kcas: {self.kcas}
                kerberos_as: {self.kerberos_as}
                kerberos_tgs: {self.kerberos_tgs}
                client: {self.client}
                current_connection: {self.current_connection}
                id_min: {self.id_min}, id_max: {self.id_max}
                """