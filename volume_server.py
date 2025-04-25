import random
import socket
from threading import Thread
import pickle
from storage.AfsFiles import  *
from kerberos.base.protocol import send, recv
from kerberos.base.msg import command
from kerberos.msg import *
QUEUE_SIZE = 10
IP = '127.0.0.1'
PORT = 22353


ID_TABLE = {} #ID:user, key
USER_TABLE = {} # user : (ip,port)      maybe should do it both ways
FILES_TABLE = {}
CALLBACK_TABLE = {} # fid:[(ip,port):src, ..]
unique_callbacks = []
TGS_KEY =b'b10SXxufAOi8cMjS01nHCT1yqrEgcCmtCJ7rL9tlnXg='
ID_MIN,ID_MAX = 0, 100000

def load_table():
    global FILES_TABLE
    f = open('./server.txt', 'rb')
    FILES_TABLE = pickle.load(f)
    f.close()

def save_table():
    f = open('./server.txt', 'wb')
    pickle.dump(FILES_TABLE, f)
    f.close()
    

def callback_message(fid):
    return command('volume_server', 'callback_broke', fid)


def server_down_message():
    return command('volume_server', 'server_down', None)


def get_file(fid):
    return FILES_TABLE.get(fid, None)


def set_table():
    dir = AfsDir('main dir', 1)
    add_to_table(dir)
    test1 = AfsFile('test1', 2, 1)
    add_to_table(test1)
    dir.add(test1)
    test2 = AfsFile('test2', 3, 12)
    add_to_table(test2)
    dir.add(test2)
    test3 = AfsFile('test3', 4, 123)
    add_to_table(test3)
    dir.add(test3)
    dir2 = AfsDir('dir2', 5)
    add_to_table(dir2)
    dir.add(dir2)
    test4 = AfsFile('test4', 6, 1234)
    add_to_table(test4)
    dir2.add(test4)
    test5 = AfsFile('test5', 7, 12345)
    add_to_table(test5)
    dir2.add(test5)
    test6 = AfsFile('test6', 8, 123456)
    add_to_table(test6)
    dir2.add(test6)


def add_to_table(file:AfsNode):
    FILES_TABLE[file.fid] = file


def handle_kerberos_setup(msg:kerberos_msg, client_socket):
    if msg.request != 'ID-REQ':
        print(f'weird {msg.request}')
    
    msg.ticket.decrypt(TGS_KEY)
    client_name = msg.ticket.client
    key = msg.ticket.key
    msg.decrypt_id(key)
    while msg.client_id in ID_TABLE.keys():
        print(f'client id : {msg.client_id}  was taken')
        new_id = get_rand_id()
        resp_msg = kerberos_msg('ID-RES', client_id=new_id)
        resp_msg.encrypt_id(key)
        send(client_socket, resp_msg)
        msg = recv(client_socket)
        msg.decrypt_id(key)
    
    resp_msg = kerberos_msg('ID-CONFIRM')
    resp_msg.encrypt_id(key)
    send(client_socket, resp_msg)
    ID_TABLE[msg.client_id] = (client_name, key)
    print(f'id was closed on {msg.client_id}:{ID_TABLE[msg.client_id]}')
    return


def handle_kerberos_wrap(msg:kereboros_wrap):
    id = msg.id
    user, key = ID_TABLE[id]
    data = msg.get_msg(key)
    if not type(data) is command:
        print(f'idk type(data)= {type(data)}')
        return None
    if user != data.sender:
        print(f'user dont match {user} / {data.sender}')
        return None
    return  data


def get_rand_id():
        rand = random.randint(ID_MIN,ID_MAX)
        while rand in ID_TABLE.keys():
            rand = random.randint(ID_MIN, ID_MAX)
        return rand


def handle_connection(client_socket, client_address):
    print('got connection from', client_address)
    msg = recv(client_socket)
    if type(msg) is kerberos_msg:
        handle_kerberos_setup(msg, client_socket)
    else:
        msg = handle_kerberos_wrap(msg)
        print(f'msg after wrap {msg}')
        if not msg is None:
            if 'fetch' == msg.cmd: # fix this written bad
                if msg.data is None:
                    answer = command('volume_server', 'file_not_found', None)
                    send(client_socket, answer)
                else:    
                    fid = int(msg.data)
                    file = get_file(fid)
                    if file is None:
                        answer = command('volume_server', 'file_not_found', None)
                    else:
                        answer = command('volume_server', 'file', file.pickle_me())
                        if(CALLBACK_TABLE.get(fid, 'def') == 'def'):
                            CALLBACK_TABLE[fid] = []
                        CALLBACK_TABLE[fid].append(msg.src)
                        if msg.src not in unique_callbacks:
                            unique_callbacks.append(msg.src)
                    send(client_socket, answer)
            elif 'write' == msg.cmd:
                pass
            elif 'change' == msg.cmd: # for testing
                if msg.data is not None:
                    fid = int(msg.data)
                    update_callbacks(fid)
        else:
            print('smth went wrong in kerb wrap')
    client_socket.close()
    return


def server_down():
    for i in unique_callbacks:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(i)
        send(s, server_down_message())
        s.close()


def update_callbacks(fid):
    for i in CALLBACK_TABLE.get(fid, None):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(i)
        send(s, callback_message(fid))
        s.close()


def print_table():
    for i, j in FILES_TABLE.items():
        print(i, j)


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
        server_down()
        server_socket.close()
    

if __name__ == "__main__":
    # Call the main handler function
    # set_table() 
    load_table()
    print_table()
    # save_table()

    main()