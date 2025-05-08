"""
cachemanager:
testAuth()
getfile()

handale callbacks
"""
import logging
import socket
from threading import Thread
from CacheManager.handlers import handle_connection
from kerberos.base.msg import command
from CacheManager.network import PORT, IP, QUEUE_SIZE
from kerberos.client import client_kerberos_socket

KERBEROS_AS_ADDRESS = ('127.0.0.1', 22356)

logger = logging.getLogger(__name__)

def main():
    """
        Main function to open a socket and wait for clients.

        :return: None
    """
    FORMAT = '%(asctime)s %(filename)s: %(message)s'
    logging.basicConfig(filename='CacheManager.log', level=logging.INFO, format=FORMAT)
    logger.info('Started ')
    client_socket_init = client_kerberos_socket(client='rugh1', password='pass1', kerberos_as=KERBEROS_AS_ADDRESS)
    command.user = 'rugh1'
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
        logger.info('Finished')

if __name__ == "__main__":
    with open('client.txt', 'w') as f: # clear client.txt
        pass
    main()
    