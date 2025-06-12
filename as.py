import socket
import sqlite3
import logging
from threading import Thread
import kerberos.base.protocol as protocol
from kerberos.msg import *
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import random

QUEUE_SIZE = 10
IP = '127.0.0.1'
PORT = 22356

logger = logging.getLogger(__name__)
tgs_addres = ('127.0.0.1', 22357)

key_st = b'TurzkQ5B4mbZ7TCMwpt3m3js3q5WumWc40OxOnNrgjg=' # shared key as&tgs

def handle_connection(client_socket, client_address):
    """
    handle_connection()

    Parameters:
        client_socket: socket.socket
            The socket connected to the client.
        client_address: tuple
            A (IP, PORT) tuple representing the client's address.

    Returns:
        None

    Description:
        Routes incoming messages from the client to either sign-in or sign-up handlers based on message type.
    """
    logger.info(f'recived connection {client_address}')
    msg:kerberos_msg = protocol.recv(client_socket)
    logger.info(f'recived msg {msg}')
    if msg.request == 'AS-REQ':
        handle_as_req(msg, client_socket)
    elif msg.request == 'AS-SIGNUP':
        pass
    else:
        logger.error(f'didnt recive AS-REQ recived : {msg.request}')
        print(f'idk wtf {msg.request}')
    client_socket.close()
    return

def handle_as_req(msg, client_socket):
    """
    handle_as_req()

    Parameters:
        msg: kerberos_msg
            The AS-REQ message received from the client.
        client_socket: socket.socket
            The socket connected to the client.

    Returns:
        None

    Description:
        Authenticates the username (by retrieving from the database), sends an initial AS-RES response (encrypted),
        waits for the client's reply, decrypts it, and invokes give_tgt() if the communication is valid.
    """
    try:
        kas = get_key_from_username(msg.client)
        if kas is None:
            resp = kerberos_msg('KRB-ERROR', 'username not found')
            protocol.send(client_socket, resp)
            return
        rand = random.randint(0, 1000)
        resp = kerberos_msg('AS-RES', client_name=rand)
        resp.encrypt_msg(kas)
        protocol.send(client_socket, resp)
        client_socket.settimeout(10.0) # so wont get stuck here
        msg_recived = protocol.recv(client_socket)
        msg_recived.decrypt_msg(kas)
        if msg_recived.client_id == rand+1:
            give_tgt(msg, client_socket, kas) 
    except Exception as err:
        print(f'encounterd err : {str(err)}')

def give_tgt(msg, client_socket, kas):
    """
    give_tgt()

    Parameters:
        msg: kerberos_msg
            The decrypted AS-REQ message from the client.
        client_socket: socket.socket
            The socket connected to the client.
        kas: bytes
            The user's secret key (K_cas).

    Returns:
        None

    Description:
        Generates a new session key (temp_key), builds an encrypted Ticket Granting Ticket (TGT) using temp_key,
        wraps it in an AS-RES Kerberos message, and sends it back to the client.
    """
    temp_key = gen_key()
    tgt = gen_tgt(temp_key, msg.client)
    resp = kerberos_msg('AS-RES', session_key=temp_key, ticket=tgt, target=tgs_addres)
    logger.info(f'resp not encrypted {resp}')
    resp.encrypt_msg(kas)
    protocol.send(client_socket, resp)


def handle_signup(msg, connected_socket):
    pass    

    
def gen_tgt(temp_key, client_name):
    """
    gen_tgt()

    Parameters:
        temp_key: bytes
            A temporary session key.
        client_name: str
            The client's username for whom the ticket is issued.

    Returns:
        Ticket
            A new Ticket object encrypted with the server's key (key_st).

    Description:
        Constructs a new Ticket object containing temp_key and client_name, encrypts it using the server key,
        and returns the encrypted ticket.
    """
    genereated_ticket = ticket(temp_key, client_name)
    logger.info(f'gen tgt {genereated_ticket}')
    genereated_ticket.encrypt(key_st)
    logger.info(f'enc tgt {genereated_ticket}')
    return genereated_ticket


def gen_key():
    """
    gen_key()

    Parameters:
        None

    Returns:
        bytes
            A newly generated session key (using Fernet.generate_key()).

    Description:
        Creates and returns a random session key suitable for Kerberos encryption.
    """
    tempkey = Fernet.generate_key()
    logger.info(f'generated key :{tempkey}')
    return tempkey

def get_key_from_username(username):
    """
    get_key_from_username()

    Parameters:
        username: str
            The username to look up in the database.

    Returns:
        bytes or None
            The hashed password (encryption key) for the user from the users table, or None if not found.

    Description:
        Retrieves the user's encryption key from the database based on the provided username.
    """
    logger.info(f'receving key from username {username}')
    con = sqlite3.connect("as_users.db")
    cur = con.cursor()
    cur.execute("select pass from users where name = ?", (username,))
    result = cur.fetchone()
    con.close()
    if result:
        return result[0]
    else:
        logger.warning(f'No user found with username: {username}')
        return None

def create_user_table():
    conn = sqlite3.connect("as_users.db")
    cursor = conn.cursor()

    # Create table with `username` as PRIMARY KEY and `password` as BLOB
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        name TEXT PRIMARY KEY,
        pass BLOB NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def add_user(username, hashed_password):
    """
    add_user()

    Parameters:
        username: str
            The new user's username.
        hashed_password: bytes
            The hashed password to store for the user.

    Returns:
        None

    Description:
        Adds a new user entry to the users table with the given username and hashed password.
    """
    con = sqlite3.connect('as_users.db')
    cur = con.cursor()
    cur.execute("INSERT INTO users (name, pass) VALUES (?, ?)", (username, hashed_password))
    con.commit()
    con.close()

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
    # print(get_key_from_username('rugh1'))
    # create_user_table()
    # add_user('rugh1', b'GRPOqXcnBK5EH7u18zAr5E2I6wtVa6J6MKFsAR0JdYk=')
    main()
    # print('a')