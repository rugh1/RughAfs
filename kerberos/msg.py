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