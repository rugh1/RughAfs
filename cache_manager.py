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
from tkintertest import LoginSignUpApp

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
    login_status = False
    app = LoginSignUpApp()
    result = app.run()  # waits until user submits and closes
    app.close_app()
    print(result)
    client_socket_init = client_kerberos_socket(client=result['username'], password=result['password'], kerberos_as=KERBEROS_AS_ADDRESS)
    login_status = client_socket_init.login()
    while login_status == 0:
        app = LoginSignUpApp()
        result = app.run() 
        client_socket_init.client = result['username']
        client_socket_init.kcas = client_kerberos_socket.hash_pass(result['password'])
        login_status = client_socket_init.login()
        app.close_app()
    if login_status == -1:
        print('AS server is unreachable')
        return 
    command.user = result['username']
    # try:
    #     client_thread = Thread(target=handle_client,
    #                         args=(('127.0.0.1', CLIENT_SERVER_PORT), 1))
    #     volume_server_thread = Thread(target=handle_volume_server,
    #                         args=((IP, PORT), QUEUE_SIZE))
    #     client_thread.start() #start client thread
    #     volume_server_thread.start() # start volume thread

    #     client_thread.join()
    #     volume_server_thread.join()
    # except socket.error as err:
    #     print('received socket exception - ' + str(err))
        


if __name__ == "__main__":
    # assert clear_cache()
    # assert clear_virtual_cache()
    main()