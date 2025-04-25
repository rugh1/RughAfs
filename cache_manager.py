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
from CacheManager.handlers import handle_connection
from kerberos.base.protocol import send, recv
from kerberos.base.msg import command
from storage.AfsFiles import AfsFile, AfsDir, AfsNode
from CacheManager.network import PORT, IP, QUEUE_SIZE




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
    with open('client.txt', 'w') as f: # clear client.txt
        pass
    main()
    