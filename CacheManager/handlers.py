 # handler.py
import logging
import os
import socket
import threading
from CacheManager.network import get_volume_server
from kerberos.msg import kerberos_wrap
from kerberos.base.msg import command
from kerberos.client import client_kerberos_socket
from CacheManager.commands import open_file, write_file, check_write_access
from kerberos.base.protocol import send, recv, client_recv, send_client
from CacheManager.tables import *

logger = logging.getLogger(__name__)

LOCK = threading.Lock()
def get_pid_bytes():
    pid = os.getpid()
    return pid

def get_pid_bytes():
    """
    get_pid_bytes()

    Parameters:
        None

    Returns:
        int
            The PID of the currently running process.

    Description:
        Retrieves and returns the process identifier (PID) of the running process.
    """
    pid = os.getpid()
    return pid

def handle_client_msg(client_socket):
    """
    handle_client_msg()

    Parameters:
        client_socket: socket.socket
            A socket object connected to the client.

    Returns:
        None

    Description:
        Processes incoming messages from a connected client over the given socket.
    """
    
    logger.info('recived client connection')
    msg = client_recv(client_socket)
    status = None
    if msg == 'PID':
        status = get_pid_bytes()
    msgs = msg.split(' ')
    print('msg:', msg)
    logger.info('handeling client msg')
    print('printing the msg[0] :' , msgs[0])
    if 'desktop.ini' in msg:   
        status = 1
    elif msgs[0] == 'open':
        print(msgs[0] == 'open')
        msg.replace('.~tmp', '')
        status = open_file(msgs[1]) #later
    elif msgs[0] == 'write1':
        msg.replace('.~tmp', '')
        print(f'checking access rights for {msgs[1]}')
        status = check_write_access(msgs[1])
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
        # clear_callback()
        # clear_fid()
    if status is None:
        status = 0
        
    send_client(client_socket, status)
    client_socket.close()

    #later

def handle_volume_server_msg(client_socket):
    """
    handle_volume_server_msg()

    Parameters:
        client_socket: socket.socket
            A socket object connected to the volume server.

    Returns:
        None

    Description:
        Processes incoming messages from the volume server over the given socket.
    """    
    msg = recv(client_socket)
    msg = client_kerberos_socket().translate_kerb_wrap(msg)
    logger.info('handeling volume server')
    if msg.cmd == 'callback_broke':
        set_callback(msg.data ,False)

def handle_client(addr, QUEUE_SIZE):
    """
    handle_client()

    Parameters:
        addr: tuple
            A (host, port) tuple indicating the IP address and port to listen on,
            e.g., ('0.0.0.0', 25565).
        QUEUE_SIZE: int
            The maximum number of pending client connections in the backlog.

    Returns:
        None

    Description:
        Listens for incoming client connections on the specified address and port,
        accepts them, and dispatches each connection for handling.
    """
    print(f'in handle_client recived {addr} , {QUEUE_SIZE}')
    try:   
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(addr)
        server_socket.listen(QUEUE_SIZE)
        while True: #loop to get connects from clients
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_client_msg, 
                        args=(client_socket, )) # send to handle client msg
            thread.start()
    except socket.error as err:
        print('received socket exception - ' + str(err))
    finally:
        server_socket.close()
        logger.info('Finished')

def handle_volume_server(addr, QUEUE_SIZE):
    """
    handle_volume_server()

    Parameters:
        addr: tuple
            A (host, port) tuple indicating the IP address and port to listen on,
            e.g., ('0.0.0.0', 25565).
        QUEUE_SIZE: int
            The maximum number of pending connections from the file server in the backlog.

    Returns:
        None

    Description:
        Listens for incoming connections from the file/volume server on the specified
        address and port, accepts them, and dispatches each connection for handling.
    """
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


