import socket
import logging
from threading import Thread
import kerberos.base.protocol as protocol
from kerberos.msg import *
from cryptography.fernet import Fernet
QUEUE_SIZE = 10
IP = '127.0.0.1'
PORT = 22356

logger = logging.getLogger(__name__)
tgs_addres = ('127.0.0.1', 22357)
key_st = b'TurzkQ5B4mbZ7TCMwpt3m3js3q5WumWc40OxOnNrgjg=' # shared key as&tgs


def handle_connection(client_socket, client_address):
    logger.info(f'recived connection {client_address}')
    msg:kerberos_msg = protocol.recv(client_socket)
    logger.info(f'recived msg {msg}')
    if msg.request == 'AS-REQ':
        kas = get_key_from_username(msg.client)
        temp_key = gen_key()
        tgt = gen_tgt(temp_key, msg.client)
        resp = kerberos_msg('AS-RES', session_key=temp_key, ticket=tgt, target=tgs_addres)
        logger.info(f'resp not encrypted {resp}')
        resp.encrypt_msg(kas)
        protocol.send(client_socket, resp)
    else:
        logger.error(f'didnt recive AS-REQ recived : {msg.request}')
        print(f'idk wtf {msg.request}')
    client_socket.close()
    return


def gen_tgt(temp_key, client_name):
    genereated_ticket = ticket(temp_key, client_name)
    logger.info(f'gen tgt {genereated_ticket}')
    genereated_ticket.encrypt(key_st)
    logger.info(f'enc tgt {genereated_ticket}')
    return genereated_ticket


def gen_key():
    tempkey = Fernet.generate_key()
    logger.info(f'generated key :{tempkey}')
    return tempkey

def get_key_from_username(username):
    #need to setup db for user with hashed passwords
    logger.info(f'receving key from username {username}')
    return b'NLZGwvHzDDMgntjYdR1u4bZ7DhgsUdP5Sph9UCYIJoE=' 


def main():
    """
        Main function to open a socket and wait for clients.

        :return: None
        """
    
    FORMAT = '%(asctime)s AS: %(message)s'
    logging.basicConfig(filename='kerberos.log', level=logging.INFO, format=FORMAT)
    logger.info('Started ')
    

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
    main()