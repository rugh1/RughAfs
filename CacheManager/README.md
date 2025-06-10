# Documentation for Python Files in 'CacheManager'

This document contains the content of all Python (.py) files found in this directory and its subdirectories.

## commands.py

python
#commands.py
import logging
from CacheManager.data_access import need_fetch
from CacheManager.network import fetch_file, get_volume_server, write_message
from CacheManager.tables import get_fid, set_callback
from kerberos.base.msg import command
from kerberos.client import client_kerberos_socket
from CacheManager.data_access import get_actual_file
logger = logging.getLogger(__name__)

def open_file(path:str):
    """
    open_file()

    Parameters:
        path: str
            The file path.

    Returns:
        int
            Status code: 0 for success, 1 for failure.

    Description:
        Handles the entire open operation from start to finish and returns whether it succeeded or failed.
    """
    file_path_start = need_fetch(path)
    logger.info(f'open_file {path} starts from {file_path_start}')
    if file_path_start is not None:
        print('fetching files')
        status = fetch_file(file_path_start, path)
        if status:
            status = 0
        else: 
            status = 1
    else:
        print(f'{path} already in cache')
        logger.info(f'file was already in cache')
        status = 0
    return status


def write_file(path:str):
    """
    write_file()

    Parameters:
        path: str
            The file path.

    Returns:
        bool
            True if the write operation succeeded, False otherwise.

    Description:
        Handles the entire write operation from start to finish and returns whether it succeeded or failed.
    """
    print(f'write path : {path}')
    logger.info(f'write path : {path}')
    print('gettign actual file')
    data = get_actual_file(path)
    a = need_fetch(path)
    if need_fetch(path) is None:
        fid = get_fid(path)
        server = get_volume_server(fid)
        client_socket = client_kerberos_socket()
        client_socket.connect(server)
        client_socket.send(write_message(fid, data))
        resp = client_socket.recv()
        logger.info(f'write respond {resp}')
        print(f'write respond {resp}')
        if resp.cmd == 'dont have write accsess':
            set_callback(fid ,False)
        client_socket.close()
        return resp.data
    else:
        print('idk  ' + a)
        logger.error('idk what to do with this rn')
        return False #MAYBE ADD ERR CODE

## data_access.py

python
# data_acsess.py
import os
import shutil
from storage.AfsFiles import AfsNode, AfsDir
from CacheManager.tables import *
import logging

logger = logging.getLogger(__name__)
ROOT_DIR = './cache_files'
VIRTUAL_ACCSESS_DIR = './ToAfs'

def set_virtual_file(file:AfsNode, path):
    """
    set_virtual_file()

    Parameters:
        file: AfsNode
            An AfsNode object representing a file or directory in the AFS structure.
        path: str
            The relative path within the virtual structure (e.g., '/dir1/file.txt', 
            not 'C:/foo/dir1/file.txt').

    Returns:
        None

    Description:
        Creates an empty virtual representation (file or directory) at the appropriate 
        location for display purposes.
    """
    if file.name == 'main dir':
        return
    actual_path = VIRTUAL_ACCSESS_DIR + path
    if type(file) is AfsDir:
        if not os.path.exists(actual_path):
            print('creating folder :', actual_path)
            os.makedirs(actual_path)
        return
    actual_path += '/' + file.name
    if type(file) is AfsNode:
        print('virtual file: ' + actual_path, file)
    with open(actual_path, 'w'):
        pass


def clear_cache():
    """
    clear_cache()

    Parameters:
        None

    Returns:
        bool
            True if the cache directory (ROOT_DIR) was successfully cleared; False otherwise.

    Description:
        Deletes all files and folders in the cache directory (ROOT_DIR).
    """
    for filename in os.listdir(ROOT_DIR):
        file_path = os.path.join(ROOT_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
            return False
    return True


def clear_virtual_cache():
    """
    clear_virtual_cache()

    Parameters:
        None

    Returns:
        bool
            True if the virtualization directory (VIRTUAL_ACCESS_DIR) was successfully cleared; False otherwise.

    Description:
        Deletes all files and folders in the virtualization directory (VIRTUAL_ACCESS_DIR).
    """
    for filename in os.listdir(VIRTUAL_ACCSESS_DIR):
        file_path = os.path.join(VIRTUAL_ACCSESS_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
            return False
    return True

def get_actual_file(path):
    """
    get_actual_file()

    Parameters:
        path: str
            The relative path within ROOT_DIR.

    Returns:
        bytes
            The full binary content of the file from the local cache.

    Description:
        Reads and returns the binary content of a file from the local cache.
    """
    print('in get real file')
    actual_path = ROOT_DIR + path
    f = open(actual_path, 'rb')
    data = f.read()
    f.close()
    return data

def cache_files(data:AfsNode, path):
    """
    cache_files()

    Parameters:
        data: AfsNode
            An AfsNode object representing a file or directory.
        path: str
            The relative path in the local cache.

    Returns:
        None

    Description:
        Saves a file or directory to the local cache and creates a virtual representation for it.
    """
    actual_path = ROOT_DIR + path
    print('real path: ' + actual_path)
    logger.info(f'caching {data} in {path}')
    if not type(data) is AfsDir:
        print('wrote ' + f'path: {path} data: {data.data}' + "\n")
        with open(actual_path, 'wb') as file:#with open(f'{path}', 'w') as file:
            file.write(data.data)
        set_fid(f'{path}', data.fid) # i dont know if needed  later
        set_virtual_file(data, path)
        return
    
    print(f'create dir {path}' + "\n")
    if not os.path.exists(actual_path):
        os.makedirs(actual_path)
    set_fid(f'{path}', data.fid) # i dont know if needed  later
    set_virtual_file(data, path)
    for f in data.children:
        if path == '/':
            print('changing path')
            path = ''
        set_fid(f'{path}/{f.name}', f.fid)
        set_virtual_file(f, path)

def need_fetch(file_path:str):
    #returns the path that you need to start fetching from
    """
    need_fetch()

    Parameters:
        file_path: str
            The requested relative path (e.g., '/dir2/sub/file.txt').

    Returns:
        str | None
            None if the file is up to date, or the path from which a fetch should start.

    Description:
        Determines whether part of the tree needs to be downloaded and returns 
        the path from which to begin fetching, or None if no fetch is required.
    """
    paths = file_path.split('/')
    logger.info(f'in need_fetch for {file_path}')
    current_path = ''
    while '' in paths:
        paths.remove('')
    paths.insert(0, '/')
    print(f'in need fetch {paths}')
    logger.info(paths)
    for path in paths:
        current_path += f'{path}'
        logger.info(f'checking {current_path} ')
        print(f'in need fetch curr: {current_path}')
        if not file_exists(current_path): # not os.path.exists(current_path)
            current_path = current_path[:-1*len(f'{path}')]
            if current_path == '':
                current_path = '/'
            print(f'current_path2: {current_path}')
            logger.info(f'file not exists fetching from {current_path}')
            return current_path
        if callback_broke(current_path):
            print(f'callback broke for {current_path}')
            logger.info(f'callback broke for {current_path}')
            return current_path
        if current_path != '/':
            current_path+= '/'
    print('none')
    return None


def file_exists(filepath:str):
    """
    file_exists()

    Parameters:
        filepath: str
            The relative path within the cache (ROOT_DIR + filepath).

    Returns:
        bool
            True if the path exists in the local cache; False otherwise.

    Description:
        Checks whether a given file exists in the local cache.
    """
    #check if file exists
    actual_path = ROOT_DIR + filepath 
    return os.path.exists(actual_path) 
    


## handlers.py

python
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
    if msg == 'PID':
        status = get_pid_bytes()
    msgs = msg.split(' ')
    print('msg:', msg)
    logger.info('handeling client msg')
    print(msgs[0])
    if msgs[0] == 'open':
        print(msgs[0] == 'open')
        status = open_file(msgs[1]) #later
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




## network.py

python
# network.py
import socket
import pickle
from kerberos.base.protocol import send, recv
from kerberos.base.msg import command
from CacheManager.data_access import get_fid, cache_files
from CacheManager.tables import set_callback, volume_in_cache, get_address_from_cache
from kerberos.client import client_kerberos_socket

QUEUE_SIZE = 10
IP = '127.0.0.1'
PORT = 9999

def recv_files(socket:client_kerberos_socket):
    """
    recv_files()

    Parameters:
        socket: client_kerberos_socket
            A Kerberos-connected socket object used to receive messages.

    Returns:
        tuple
            (file, callback) if data was received, or (None, None) if the file was not found.

    Description:
        Reads a 'command' message from the given socket, extracts the file object (or returns None if not found),
        and returns it along with its associated callback.
    """
    data:command = socket.recv()
    if data.cmd == 'file_not_found' or data.data is None:
        return None, None
    print(data)
    file = pickle.loads(data.data)
    print(file)
    return file, None


def fetch_message(path):
    """
    fetch_message()

    Parameters:
        path: str
            The relative path of the file for which to send a fetch request.

    Returns:
        Command
            A command object of type 'fetch' containing the file identifier (fid) and source address.

    Description:
        Builds and returns a 'fetch' command message for the volume server using the specified file path.
    """
    fid = get_fid(path)
    msg = command('fetch', fid, src=(IP, PORT))
    print(msg)
    return msg

def write_message(fid, data):
    """
    write_message()

    Parameters:
        fid: str
            The file identifier to which data will be written.
        data: bytes
            The binary data to send.

    Returns:
        Command
            A command object of type 'write' that includes the fid, the data to write, and the source address.

    Description:
        Builds and returns a 'write' command message for the volume server with the provided binary data.
    """
    return command('write', (fid, data), src=(IP, PORT))


def fetch_file(filepath_start:str, file_path:str,):
    """
    fetch_file()

    Parameters:
        filepath_start: str
            The relative path from which to start the fetch (e.g., '/dir1').
        file_path: str
            The full relative path of the file to retrieve (e.g., '/dir1/sub/file.txt').

    Returns:
        bool
            True if all files were successfully saved to the cache; False if an error occurred.

    Description:
        Recursively performs a fetch operation from the volume server, starting at 'filepath_start' and
        continuing until 'file_path' is retrieved. Saves each file into the local cache and updates callbacks.
    """
    try:
        server = get_volume_server(get_fid((filepath_start)))
        if server is None:
            print('failed getting volume server')
            return False 
        
        client_socket = client_kerberos_socket()
        status = client_socket.connect(server)
        if status == False:
            raise Exception('faild to connect') 
        #fetch first dir/file
        print('sending first fetch')
        client_socket.send(fetch_message(filepath_start))
        files, callback = recv_files(client_socket)
        if files is None:
            print(f'server failed to find file {filepath_start}, {get_fid(filepath_start)}')
            raise Exception(f'server failed to find file')
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
            current_path += '/' + path
            server = get_volume_server(get_fid((current_path)))
            if server is None:
                print('failed getting server')
                return False
            client_socket = client_kerberos_socket()
            connection_status = client_socket.connect(server) #
            if connection_status == False:
                raise Exception('faild to connect') 
            print(current_path)
            client_socket.send(fetch_message(current_path))
            files, callback = recv_files(client_socket)
            if files is None:
                print(f'{current_path} wasnt found')
                raise Exception('failed to find file')
            cache_files(files, current_path)
            set_callback(get_fid(current_path))
            client_socket.close()
        print('sucsess in fetch file')
    except Exception as err:
        print(f'encounterd err : {str(err)}')
        client_socket.close()
        return False
    return True


def get_volume_server(fid:str):
    """
    get_volume_server()

    Parameters:
        fid: str
            The file identifier (e.g., '2-123'), which includes the volume number.

    Returns:
        tuple
            A tuple (IP, PORT) of the corresponding volume server.

    Description:
        Extracts the volume number from the given fid and calls get_address_from_volume to obtain
        the IP address and port of the appropriate volume server.
    """
    volume = int(fid.split('-')[0])

    print(f'in get_volume_server {volume}')
    return get_address_from_volume(volume)

def get_address_from_volume(volume):
    """
    get_address_from_volume()

    Parameters:
        volume: int
            The volume number (e.g., 2).

    Returns:
        tuple
            A tuple (IP, PORT) of the volume server corresponding to the given volume.

    Description:
        Retrieves and returns the IP address and port for the specified volume number.
    """
    print('get_address_from_volume')
    if volume_in_cache(volume):
        return get_address_from_cache(volume)
    return get_address_from_db(volume)


def get_address_from_db(volume):
    pass

    

## tables.py

python
import threading
import logging
#tables
FID_TABLE = {'/': '1-1'}
CALLBACK_TABLE = {} #FID:TRUE(IF FINE)/FALSE(IF NOT FINE)
LOCK = threading.Lock()
VOLUME_TABLE = {1:('127.0.0.1', 22353)}
logger = logging.getLogger(__name__)


def get_fid(current_path):
    """
    get_fid()

    Parameters:
        current_path: str
            The relative path of the file or directory (used as the key in FID_TABLE).

    Returns:
        str or None
            The fid found in FID_TABLE for the given current_path, or None if not present.

    Description:
        Retrieves the fid associated with the specified current_path from the FID_TABLE.
    """
    print(f'getting fid {current_path}')
    logger.info(f'getting fid {current_path} {FID_TABLE.get(current_path, None)}')
    return FID_TABLE.get(current_path, None)

def set_fid(key, value):
    """
    set_fid()

    Parameters:
        key: str
            The relative path of the file or directory to map to an fid.
        value: any
            The fid to assign for the given key.

    Returns:
        None

    Description:
        Inserts or updates the entry in FID_TABLE, mapping the given key to the specified value.
    """
    print(f'setting fid {key}:{value}')
 
    logger.info(f'setting fid {key}:{value}')
    FID_TABLE[key] = value

def get_callback():
    """
    get_callback()

    Parameters:
        None

    Returns:
        dict
            The entire CALLBACK_TABLE structure, containing callback status for each fid.

    Description:
        Returns the current CALLBACK_TABLE, which tracks whether callbacks are “broken” for each fid.
    """
    return CALLBACK_TABLE

def callback_broke(path):
    """
    callback_broke()

    Parameters:
        path: str
            The relative path of the file or directory whose callback status is being checked.

    Returns:
        bool
            True if the callback is broken for the specified path; False otherwise.

    Description:
        Checks whether the callback has “broken” for the given file or directory, based on CALLBACK_TABLE.
    """
    fid = get_fid(path)
    LOCK.acquire() # ? later
    a = CALLBACK_TABLE.get(fid, False)
    LOCK.release() # ? later
    return not a

def set_callback(key, value:bool = True):
    """
    set_callback()

    Parameters:
        key: str
            The fid for which to update the callback status in CALLBACK_TABLE.
        value: bool
            The new callback status (True = broken, False = intact).

    Returns:
        None

    Description:
        Updates CALLBACK_TABLE by setting the callback status for the given key to the specified value.
    """
    LOCK.acquire() # ? later
    f'setting callback {key}:{value}'
    CALLBACK_TABLE[key] = value
    LOCK.release()

def volume_in_cache(volume):
    """
    volume_in_cache()

    Parameters:
        volume: int
            The volume number to check for existence in VOLUME_TABLE.

    Returns:
        bool
            True if the specified volume exists in VOLUME_TABLE; False otherwise.

    Description:
        Checks whether the given volume number is present in VOLUME_TABLE.
    """
    print(volume)
    print(f'volume in cache: {volume}, {VOLUME_TABLE.keys()}  {volume in (VOLUME_TABLE.keys())}')
    return volume in VOLUME_TABLE.keys()

def get_address_from_cache(volume):
    return VOLUME_TABLE.get(volume, None)

