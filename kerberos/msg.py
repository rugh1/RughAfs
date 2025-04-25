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
        self.client = super().encrypt(self.client, key)
        self.target = super().encrypt(self.target, key)
        self.session_key = super().encrypt(self.session_key, key)

    def encrypt_id(self, key):
        self.client = super().encrypt(self.client, key)
        self.target = super().encrypt(self.target, key)
        self.session_key = super().encrypt(self.session_key, key)
        self.client_id = super().encrypt(self.client_id, key)

    def decrypt_msg(self, key):
        self.client = super().decrypt(self.client, key)
        self.target = super().decrypt(self.target, key)
        self.session_key = super().decrypt(self.session_key, key)
        

    def decrypt_id(self, key):
        self.client = super().decrypt(self.client, key)
        self.target = super().decrypt(self.target, key)
        self.session_key = super().decrypt(self.session_key, key)
        self.client_id = super().decrypt(self.client_id, key)

    def __str__(self):
        return f"""
                request: {self.request}
                client: {self.client}
                client_id: {self.client_id}
                target: {self.target}
                session_key: {self.session_key}
                ticket: {self.ticket}
                """


class kereboros_wrap(encr):
    def __init__(self, id, msg, key):
        self.id = id 
        self.msg = self.encrypt(pickle.dumps(msg), key)

    def get_msg(self, key):
        return pickle.loads(self.msg.decrypt(key))
    
    
class ticket(encr):
    def __init__(self, key, client):
        self.key = key
        self.client = client
    
    def encrypt(self, key):
        self.key = super().encrypt(self.key, key)
        self.client = super().encrypt(self.key, key)

    def decrypt(self, key):
        self.key = super().decrypt(self.key, key)
        self.client = super().decrypt(self.key, key)
