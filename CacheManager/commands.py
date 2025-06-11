#commands.py
import logging
from CacheManager.data_access import need_fetch
from CacheManager.network import fetch_file, get_volume_server, write_message, access_message
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
    path = path.replace('\\', '/')
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
    
def check_write_access(path):
    """
    check_write_access)

    Parameters:
        path: str
            The file path.

    Returns:
        bool
            returns -1 if user doesnt have write access else returns whatever really

    Description:
        checks write access of a file for user
    """
 
    print(f'check access for path : {path}')
    logger.info(f'check access path : {path}')
    a = need_fetch(path)
    if need_fetch(path) is None:
        fid = get_fid(path)
        server = get_volume_server(fid)
        client_socket = client_kerberos_socket()
        client_socket.connect(server)
        client_socket.send(access_message(fid))
        resp = client_socket.recv()
        logger.info(f'write respond {resp}')
        print(f'write respond {resp}')
        if resp.cmd != 'access_check':
            logger.error(f'smth wierd with {resp}')
            return -1
        client_socket.close()
        return resp.data
    else:
        print('idk  ' + a)
        logger.error('idk what to do with this rn')
        return -1 
 
    
    
      