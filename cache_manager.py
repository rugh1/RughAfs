"""
cachemanager:
testAuth()
getfile()

handale callbacks
"""
import logging
import socket
from threading import Thread
from CacheManager.data_access import clear_cache, clear_virtual_cache
from CacheManager.handlers import handle_client, handle_volume_server
from kerberos.base.msg import command
from CacheManager.network import PORT, IP, QUEUE_SIZE
from kerberos.client import client_kerberos_socket
import os, shutil

KERBEROS_AS_ADDRESS = ('127.0.0.1', 22356)
CLIENT_SERVER_PORT = 9998;
logger = logging.getLogger(__name__)


def main():
    """
        Main function to open a socket and wait for clients.

        :return: None
    """
    FORMAT = '%(asctime)s %(filename)s: %(message)s'
    logging.basicConfig(filename='CacheManager.log', level=logging.INFO, format=FORMAT)
    logger.info('Started ')
    client_socket_init = client_kerberos_socket(client='rugh1', password='rugh1', kerberos_as=KERBEROS_AS_ADDRESS)
    print(f'logging in:{client_socket_init.login()}')
    command.user = 'rugh1'
    try:
        client_thread = Thread(target=handle_client,
                            args=(('127.0.0.1', CLIENT_SERVER_PORT), 1))
        volume_server_thread = Thread(target=handle_volume_server,
                            args=((IP, PORT), QUEUE_SIZE))
        client_thread.start()
        volume_server_thread.start()

        client_thread.join()
        volume_server_thread.join()
    except socket.error as err:
        print('received socket exception - ' + str(err))
        


if __name__ == "__main__":
    assert clear_cache()
    assert clear_virtual_cache()
    main()