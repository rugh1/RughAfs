"""
cachemanager:
testAuth()
getfile()

handale callbacks
"""
import os
import socket
import pickle
from threading import Thread
import threading
from protocol import send, recv
from msg import command
from AfsFile import AfsFile, AfsDir, AfsNode

QUEUE_SIZE = 10
IP = '127.0.0.1'
PORT = 9999

FID_TABLE = {'/': 1}
CALLBACK_TABLE = {} #FID:TRUE(IF FINE)/FALSE(IF NOT FINE)
LOCK = threading.Lock()

def recv_files(socket):
    data = recv(socket)
    print(data)
    file = pickle.loads(data.data)
    print(file)
    return file, None


def cache_files(data:AfsNode, path):
    if not type(data) is AfsDir:
        print('wrote ' + f'path: {path} data: {f.data}' + "\n")
        with open('./client.txt', 'a') as file:#with open(f'{path}', 'w') as file:
            file.write(f'path: {path} data: {f.data}' + "\n")#file.write(f.data + "\n")
        return
    
    print('wrote ' + f'dir {data.name} {data.fid}: {path}' + "\n")
    with open('./client.txt', 'a') as file:#instad of os.makedirs(f'{path}', exist_ok=True)
        file.write(f'dir {data.name} {data.fid}: {path}' + "\n")#os.makedirs(f'{path}', exist_ok=True)
    
    FID_TABLE[f'{path}'] = data.fid

    for f in data.children:
        if path == '/':
            print('changing path')
            path = ''
        if type(f) is AfsDir:
            print('wrote ' + f'{path}/{f.name}' + "\n")
            with open('./client.txt', 'a') as file:#instad of os.makedirs(f'{path}/{f.name}', exist_ok=True)
                file.write(f'{path}/{f.name}' + "\n")#os.makedirs(f'{path}/{f.name}', exist_ok=True)
        else:
            print(f'path: {path}/{f.name} data: {f.data}' + "\n")
            with open('./client.txt', 'a') as file:#with open(f'{path}/{f.name}', 'w') as file:
                file.write(f'path: {path}/{f.name} data: {f.data}' + "\n")#file.write(f.data + "\n")
        FID_TABLE[f'{path}/{f.name}'] = f.fid


def callback_broke(path):
    fid = get_fid(path)
    LOCK.acquire() # ?
    a = CALLBACK_TABLE.get(fid, False)
    LOCK.release() # ?
    return not a


def get_fid(current_path):
    print(current_path)
    return FID_TABLE[current_path]


def get_volume_server(file_path:str):
    return('127.0.0.1', 22353)


def fetch_message(path):
    fid = get_fid(path)
    msg = command('client', 'fetch', fid)
    print(msg)
    return msg


def need_fetch(file_path:str):
    f = open('./client.txt', 'r')
    paths = file_path.split('/')
    current_path = ''
    while '' in paths:
        paths.remove('')
    if len(paths) == 0:
        print('app')
        paths.append('')
    for path in paths:
        current_path += f'/{path}'
        print(current_path)
        if current_path not in f.read(4000): # not os.path.exists(current_path)
            current_path = current_path[:-1*len(f'/{path}')]
            if current_path == '':
                current_path = '/'
            print(f'current_path2: {current_path}')
            f.close()
            return current_path
        # if callback_broke(current_path):
        #     f.close()
        #     return current_path
    f.close()
    print('none')
    return None

def fetch_file(server, filepath_start:str, file_path:str,): 
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(server)

    #fetch first dir/file
    send(client_socket, fetch_message(filepath_start))
    files, callback = recv_files(client_socket)
    cache_files(files, filepath_start)
    #handle_callback(callback)

    file_path = file_path.replace(filepath_start, '', 1)
    current_path = filepath_start

    #cache files as you go
    for path in file_path:
        current_path += '/' + path
        send(client_socket, fetch_message(current_path))
        files, callback = recv_files(client_socket)
        cache_files(files, current_path)
        #handle_callback(callback)

    client_socket.close()
    return

def open_file(path:str, mode:str):
    file_path_start = need_fetch(path)
    print(file_path_start)
    if file_path_start is not None:
        print('need fetch')
        server = get_volume_server(path)
        fetch_file(server, file_path_start, path)
    else:
        print(f'{path} already in cache')
    return

def handle_client_msg(client_socket, msg:command):
    if msg.cmd == 'open':
        open_file(msg.data, 'r') #later

    elif msg.cmd == 'list':
        print(FID_TABLE)#later
    
    client_socket.close()
    #later

def handle_volume_server(msg:command):
    if msg.cmd == 'callback_broke':
        CALLBACK_TABLE[msg.data] = False


def handle_connection(client_socket, client_address):
    print('recived connection', client_address)
    msg:command = recv(client_socket)
    print('a')
    print(msg)
    if(msg.sender == 'client'):
        handle_client_msg(client_socket , msg)
    elif(msg.sender == 'volume_server'):
        handle_volume_server(msg)


def main():
    """
        Main function to open a socket and wait for clients.

        :return: None
        """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        print("Listening for connections on port %d" % PORT)
        while True:
            client_socket, client_address = server_socket.accept()

            thread = Thread(target=handle_connection,
                            args=(client_socket, client_address))
            thread.start()

    except socket.error as err:
        print('received socket exception - ' + str(err))
    finally:
        server_socket.close()

if __name__ == "__main__":
    with open('client.txt', 'w') as f:
        pass
    main()
    