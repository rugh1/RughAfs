 # handler.py
import logging
import os
import socket
import threading
from CacheManager.network import get_volume_server
from kerberos.msg import kerberos_wrap
from kerberos.base.msg import command
from kerberos.client import client_kerberos_socket
from CacheManager.commands import open_file, write_file
from kerberos.base.protocol import send, recv, client_recv, send_client
from CacheManager.tables import *

logger = logging.getLogger(__name__)

LOCK = threading.Lock()
def get_pid_bytes():
    pid = os.getpid()
    return pid

def handle_client_msg(client_socket):
    logger.info('recived client connection')
    msg = client_recv(client_socket)
    status = None
    if msg == 'PID':
        status = get_pid_bytes()
    msgs = msg.split(' ')
    print('msg:', msg)
    logger.info('handeling client msg')
    print(msgs[0])
    if msgs[0] == 'open':
        print(msgs[0] == 'open')
        status = open_file(msgs[1], 'r') #later
    elif msgs[0] == 'write':
        print(f'write msg: {msg}')
        status = write_file(msgs[1])
    elif msgs[0] == 'list':
        print(FID_TABLE)#later
        status = True
    elif msgs[0] == 'callback':
        print(CALLBACK_TABLE)
        status = True
    elif msgs[0] == 'break_callback': # testing
        server = get_volume_server(msg.data)
        client_socket = client_kerberos_socket()
        client_socket.connect(server)
        testing_msg = command('change', msg.data)
        client_socket.send(testing_msg)

    elif msgs[0] == 'clear': #testing
        with open('client.txt', 'w') as f: # clear client.txt
            pass
        clear_callback()
        clear_fid()
    if status is None:
        status = 0
        
    send_client(client_socket, status)
    client_socket.close()

    #later

def handle_volume_server_msg(client_socket):
    msg = recv(client_socket)
    msg = client_kerberos_socket().translate_kerb_wrap(msg)
    logger.info('handeling volume server')
    if msg.cmd == 'callback_broke':
        set_callback(msg.data ,False)


# def handle_connection(client_socket, client_address):
#     logger.info(f'recived connection {client_address}')
#     print('recived connection', client_address)
#     msg = recv(client_socket)
#     if type(msg) is kerberos_wrap:
#         msg = client_kerberos_socket().translate_kerb_wrap(msg)
#     logger.info(f'recived msg: {msg}')
#     if(msg.sender == 'client'):
#         handle_client_msg(client_socket , msg)
#     elif(msg.sender == 'volume_server'):
#         handle_volume_server_msg(msg)
#     else:
#         logger.error(f'reviced from unknown sender: {msg.sender}')

def handle_client(addr, QUEUE_SIZE):
    print(f'in handle_client recived {addr} , {QUEUE_SIZE}')
    try:   
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(addr)
        server_socket.listen(QUEUE_SIZE)
        while True:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_client_msg,
                        args=(client_socket, ))
            thread.start()
    except socket.error as err:
        print('received socket exception - ' + str(err))
    finally:
        server_socket.close()
        logger.info('Finished')
# def handle_volume_server():

def handle_volume_server(addr, QUEUE_SIZE):
    try:   
        print(f'in handle_volume server recived {addr} , {QUEUE_SIZE}')
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(addr)
        server_socket.listen(QUEUE_SIZE)
        while True:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_volume_server_msg,
                        args=(client_socket, ))
            thread.start()
    except socket.error as err:
        print('received socket exception - ' + str(err))
    finally:
        server_socket.close()
        logger.info('Finished')


