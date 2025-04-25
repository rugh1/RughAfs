 # handler.py
import socket
import threading
from CacheManager.network import get_volume_server
from kerberos.base.msg import command
from CacheManager.commands import open_file
from kerberos.base.protocol import send, recv
from CacheManager.tables import *

LOCK = threading.Lock()

def handle_client_msg(client_socket, msg:command):
    if msg.cmd == 'open':
        open_file(msg.data, 'r') #later

    elif msg.cmd == 'list':
        print(FID_TABLE)#later
    elif msg.cmd == 'callback':
        print(CALLBACK_TABLE)
    
    elif msg.cmd == 'break_callback': # testing
        server = get_volume_server(msg.data)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(server)
        testing_msg = command('client', 'change', msg.data)
        send(client_socket, testing_msg)
    elif msg.cmd == 'clear':
        with open('client.txt', 'w') as f: # clear client.txt
            pass
        clear_callback()
        clear_fid()
    
    client_socket.close()

    #later

def handle_volume_server(msg:command):
    if msg.cmd == 'callback_broke':
        set_callback(msg.data ,False)


def handle_connection(client_socket, client_address):
    print('recived connection', client_address)
    msg:command = recv(client_socket)
    print('a')
    print(msg)
    if(msg.sender == 'client'):
        handle_client_msg(client_socket , msg)
    elif(msg.sender == 'volume_server'):
        handle_volume_server(msg)



