 # handler.py
import logging
import socket
import threading
from CacheManager.network import get_volume_server
from kerberos.msg import kerberos_wrap
from kerberos.base.msg import command
from kerberos.client import client_kerberos_socket
from CacheManager.commands import open_file, write_file
from kerberos.base.protocol import send, recv
from CacheManager.tables import *

logger = logging.getLogger(__name__)

LOCK = threading.Lock()

def handle_client_msg(client_socket, msg:command):
    logger.info('handeling client msg')
    print(msg.cmd)
    if msg.cmd == 'open':
        print(msg.cmd == 'open')
        open_file(msg.data, 'r') #later
    elif msg.cmd == 'write':
        print(f'write msg: {msg}')
        write_file(msg.data)
    elif msg.cmd == 'list':
        print(FID_TABLE)#later
    elif msg.cmd == 'callback':
        print(CALLBACK_TABLE)
    
    elif msg.cmd == 'break_callback': # testing
        server = get_volume_server(msg.data)
        client_socket = client_kerberos_socket()
        client_socket.connect(server)
        testing_msg = command('change', msg.data)
        client_socket.send(testing_msg)
    elif msg.cmd == 'clear':
        with open('client.txt', 'w') as f: # clear client.txt
            pass
        clear_callback()
        clear_fid()
    
    client_socket.close()

    #later

def handle_volume_server(msg:command):
    logger.info('handeling volume server')
    if msg.cmd == 'callback_broke':
        set_callback(msg.data ,False)


def handle_connection(client_socket, client_address):
    logger.info(f'recived connection {client_address}')
    print('recived connection', client_address)
    msg = recv(client_socket)
    if type(msg) is kerberos_wrap:
        msg = client_kerberos_socket().translate_kerb_wrap(msg)
    logger.info(f'recived msg: {msg}')
    if(msg.sender == 'client'):
        handle_client_msg(client_socket , msg)
    elif(msg.sender == 'volume_server'):
        handle_volume_server(msg)
    else:
        logger.error(f'reviced from unknown sender: {msg.sender}')



