import socket
from threading import Thread
import kerberos.base.protocol as protocol
from kerberos.msg import *
from cryptography.fernet import Fernet
QUEUE_SIZE = 10
IP = '127.0.0.1'
PORT = 22357


key_st = b'T1Bl-RyiMj5wJzsgUOxXyHn3pgL1k8Z79CkhrRFzcWY=' # shared key as&tgs


def handle_connection(client_socket, client_address):
    msg:kerberos_msg = protocol.recv(client_socket)
    if msg.request == 'TGS-REQ':
        tgt:ticket = msg.ticket
        tgt.decrypt()
        msg.decrypt_msg(tgt.key)
        if msg.client != tgt.client:
            print('trying to use other tgt')
            resp = kerberos_msg('KRB-ERROR', 'trying to use other tgt')
            protocol.send(resp)
            client_socket.close()
            return
        if not valid_user(msg.client, msg.target):
            print('user doesnt have acsess to service')
            resp = kerberos_msg('KRB-ERROR', 'user doesnt have acsess to service')
            protocol.send(resp)
            client_socket.close()
            return
        temp_service_key = gen_key()
        service_key = get_service_key(msg.target)
        service_ticket = gen_ticket(temp_service_key, msg.client, service_key)
        resp = kerberos_msg('TGS-RES', session_key=temp_service_key, ticket=service_ticket, )
        resp.encrypt_msg(tgt.key)
        protocol.send(resp)
    else:
        print('idk wtf ')
    client_socket.close()
    return

def get_service_key(service):
    return b'b10SXxufAOi8cMjS01nHCT1yqrEgcCmtCJ7rL9tlnXg='


def gen_ticket(temp_key, client_name, key):
    genereated_ticket = ticket(temp_key, client_name)
    genereated_ticket.encrypt(key)
    return genereated_ticket

def gen_key():
    return Fernet.generate_key()


def valid_user(username, service_name):
    return True # needs work


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
    main()