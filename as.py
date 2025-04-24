import socket
from threading import Thread
import networks.protocol as protocol
from kerberos.msg import *
QUEUE_SIZE = 10
IP = '127.0.0.1'
PORT = 22356


tgs_addres = ('127.0.0.1', 22357)
key_st = b'T1Bl-RyiMj5wJzsgUOxXyHn3pgL1k8Z79CkhrRFzcWY=' # shared key as&tgs


def handle_connection(client_socket, client_address):
    msg:kerberos_msg = protocol.recv(client_socket)
    if msg.request == 'AS-REQ':
        kas = get_key_from_username(msg.client)
        temp_key = gen_key()
        tgt = gen_tgt(temp_key, msg.client)
        resp = kerberos_msg('AS-RES', session_key=temp_key, ticket=tgt, target=tgs_addres)
        resp.encrypt_msg(kas)
        protocol.send(resp)
    else:
        print(f'idk wtf {msg.request}')
    client_socket.close()
    return


def gen_tgt(temp_key, client_name):
    genereated_ticket = ticket(temp_key, client_name)
    genereated_ticket.encrypt(key_st)
    return genereated_ticket


def gen_key():
    return Fernet.generate_key()


def get_key_from_username(username):
    #need to setup db for user with hashed passwords
    return '5a105e8b9d40e1329780d62ea2265d8a' #test1 md5


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