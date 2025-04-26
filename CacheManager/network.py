# network.py
import socket
import pickle
from kerberos.base.protocol import send, recv
from kerberos.base.msg import command
from CacheManager.data_access import get_fid, cache_files
from CacheManager.tables import set_callback
from kerberos.client import client_kerberos_socket

QUEUE_SIZE = 10
IP = '127.0.0.1'
PORT = 9999

def recv_files(socket:client_kerberos_socket):
    data:command = socket.recv()
    if data.cmd == 'file_not_found' or data.data is None:
        return None, None
    print(data)
    file = pickle.loads(data.data)
    print(file)
    return file, None


def fetch_message(path):
    fid = get_fid(path)
    msg = command('fetch', fid, src=(IP, PORT))
    print(msg)
    return msg


def fetch_file(server, filepath_start:str, file_path:str,): 
    client_socket = client_kerberos_socket()
    client_socket.connect(server)
    
    #fetch first dir/file
    print('sending first fetch')
    client_socket.send(fetch_message(filepath_start))
    files, callback = recv_files(client_socket)
    if files is None:
        print(f'server failed to find file {filepath_start}, {get_fid(filepath_start)}')
        client_socket.close()
        return
    cache_files(files, filepath_start)
    set_callback(get_fid(filepath_start))
    client_socket.close()


    file_path = file_path.replace(filepath_start, '', 1)
    file_paths = file_path.split('/')
    while '' in file_paths:
        file_paths.remove('')
    current_path = filepath_start
    if current_path[-1] == '/':
        current_path = current_path[:-1]
    print('sending next fetch', file_path)
   
    #cache files as you go
    for path in file_paths:
        client_socket = client_kerberos_socket()
        client_socket.connect(server) #later
        current_path += '/' + path
        print(current_path)
        client_socket.send(fetch_message(filepath_start))
        files, callback = recv_files(client_socket)
        if files is None:
            print(f'{current_path} wasnt found')
            client_socket.close()
            break 
        cache_files(files, current_path)
        set_callback(get_fid(current_path))
        client_socket.close()
    return


def get_volume_server(fid:str):
    return('127.0.0.1', 22353)