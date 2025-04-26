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