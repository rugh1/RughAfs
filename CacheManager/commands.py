#commands.py
import logging
from CacheManager.data_access import need_fetch
from CacheManager.network import fetch_file, get_volume_server, write_message
from CacheManager.tables import get_fid
from kerberos.base.msg import command
from kerberos.client import client_kerberos_socket

logger = logging.getLogger(__name__)

def open_file(path:str, mode:str):
    file_path_start = need_fetch(path)
    logger.info(f'open_file {path} starts from {file_path_start}')
    if file_path_start is not None:
        print('need fetch')
        server = get_volume_server(get_fid(path))
        fetch_file(server, file_path_start, path)
    else:
        print(f'{path} already in cache')
        logger.info(f'file was already in cache')
    return

def write_file(msg:str):
    print(f'write msg : {msg}')
    logger.info(f'write msg : {msg}')
    path = msg[0]
    data = msg[1]
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
    else:
        print('idk')
        logger.error('idk what to do with this rn')