#commands.py
import logging
from CacheManager.data_access import need_fetch
from CacheManager.network import fetch_file, get_volume_server, write_message
from CacheManager.tables import get_fid
from kerberos.base.msg import command
from kerberos.client import client_kerberos_socket
from CacheManager.data_access import get_actual_file
logger = logging.getLogger(__name__)

def open_file(path:str, mode:str):
    file_path_start = need_fetch(path)
    logger.info(f'open_file {path} starts from {file_path_start}')
    if file_path_start is not None:
        print('fetching files')
        status = fetch_file(file_path_start, path)
    else:
        print(f'{path} already in cache')
        logger.info(f'file was already in cache')
        status = True
    return status

def write_file(path:str):
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
        client_socket.close()
        return resp.data
    else:
        print('idk  ' + a)
        logger.error('idk what to do with this rn')
        return False #MAYBE ADD ERR CODE