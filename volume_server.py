import logging
import random
import socket
from threading import Thread
import pickle
from storage.AfsFiles import  *
from kerberos.base.protocol import send, recv
from kerberos.base.msg import command
from kerberos.msg import *

logger = logging.getLogger(__name__)

QUEUE_SIZE = 10
IP = '127.0.0.1'
PORT = 22353


ID_TABLE = {} #ID:user, key
IDSOCK_TABLE = {} # (ip, port) : id to use
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
    return command('callback_broke', fid)


def server_down_message():
    return command('server_down', None)


def get_file(fid):
    logger.info(f'getting file: { FILES_TABLE.get(fid, None)}')
    return FILES_TABLE.get(fid, None)


def change_file(fid, data):
    file = get_file(fid)
    if not type(file) is AfsFile:
        logger.error('cant change dir')
        return False
    with open(file.data, 'wb') as file:
        file.write(data)
    return True

def set_files():
    for i in range(10):
        f = open(f'./volume_server_files/test{i}.txt', 'a')
        f.write(f'hello world {i}')
        f.close()

def set_table():
    dir = AfsDir('main dir', '1-1')
    add_to_table(dir)
    for i in range(1, 4):
        test = AfsFile(f'test{i}.txt', f'1-{i+1}', f'./volume_server_files/test{i}.txt')
        add_to_table(test)
        dir.add(test)
    
    dir2 = AfsDir('dir2', '1-123')
    add_to_table(dir2)
    dir.add(dir2)
    for i in range(4, 8):
        test = AfsFile(f'test{i}.txt', f'1-{i+1}', f'./volume_server_files/test{i}.txt')
        add_to_table(test)
        dir2.add(test)


def add_to_table(file:AfsNode):
    FILES_TABLE[file.fid] = file


def handle_kerberos_setup(msg:kerberos_msg, client_socket):
    logger.info(f'setting up id')
    if msg.request != 'ID-REQ':
        print(f'weird {msg.request}')
        logger.error(f'not ID-REQ wierd {msg.request}')
    
    msg.ticket.decrypt(TGS_KEY)
    logger.info(f'ticket dec : {msg.ticket}')
    client_name = msg.ticket.client
    key = msg.ticket.key
    msg.decrypt_id(key)
    logger.info(f'msg dec : {msg}')
    while msg.client_id in ID_TABLE.keys():
        print(f'client id : {msg.client_id}  was taken')
        logger.info(f'client id : {msg.client_id}  was taken')
        new_id = get_rand_id()
        resp_msg = kerberos_msg('ID-RES', client_id=new_id)
        logger.info(f'resp {resp_msg}')
        resp_msg.encrypt_id(key)
        send(client_socket, resp_msg)
        msg = recv(client_socket)
        msg.decrypt_id(key)
    
    resp_msg = kerberos_msg('ID-CONFIRM')
    resp_msg.encrypt_id(key)
    send(client_socket, resp_msg)
    ID_TABLE[msg.client_id] = (client_name, key)
    print(f'id was closed on {msg.client_id}:{ID_TABLE[msg.client_id]}')
    logger.info(f'id was closed on {msg.client_id}:{ID_TABLE[msg.client_id]}')
    return


def handle_kerberos_wrap(msg:kerberos_wrap):
    id = msg.id
    user, key = ID_TABLE[id]
    data = msg.get_msg(key)
    if not type(data) is command:
        print(f'idk type(data)= {type(data)}')
        return None
    if user != data.sender:
        print(f'user dont match {user} / {data.sender}')
        return None
    return  data, id


def get_rand_id():
        rand = random.randint(ID_MIN,ID_MAX)
        while rand in ID_TABLE.keys():
            rand = random.randint(ID_MIN, ID_MAX)
        return rand

def wrap_cmd(id, cmd):
    logger.info(f'wrapping id: {id} data {cmd} ')
    return kerberos_wrap(id, cmd, ID_TABLE[id][1])


def get_file_data(file:AfsFile):
    f = open(file.data, 'rb')
    file_data = f.read()
    f.close()
    return file_data


def handle_fetch_cmd(msg, id):
    logger.info(f'fetch {msg}')
    if msg.data is None:
        return wrap_cmd(id, command('file_not_found', None))
       
    fid = msg.data
    file = get_file(fid)
    if file is None:
        return  wrap_cmd(id, command('file_not_found', None))
    
    if type(file) is AfsDir:
        answer = wrap_cmd(id, command('file', file.pickle_me()))
    else:
        print(file)
        file_data = get_file_data(file)
        file_to_send = AfsFile(file.name, file.fid, file_data)
        answer = wrap_cmd(id, command('file', file_to_send.pickle_me()))

    if(CALLBACK_TABLE.get(fid, 'def') == 'def'):
        logger.info(f'first callback_table set')
        CALLBACK_TABLE[fid] = []

    if msg.src not in CALLBACK_TABLE[fid]:
        CALLBACK_TABLE[fid].append(msg.src)
        logger.info(f'added {msg.src} to {fid}')

    if msg.src not in unique_callbacks:
        unique_callbacks.append(msg.src)
        IDSOCK_TABLE[msg.src] = id
        logger.info(f'added {msg.src} to uniqe_callbacks')

    return answer

def handle_write_cmd(msg, id):
    logger.info(f'fetch {msg}')
    if msg.data is None:
        answer = wrap_cmd(id, command('file_not_found', None))
    else:
        if len(msg.data) != 2:
            logger.error(f'data in write wasnt right {msg.data}')
            answer = wrap_cmd(id, command('cant write Dir', None))
            return answer
        
        fid = int(msg.data[0])
        file = get_file(fid)
        if type(file) is AfsDir:
            answer = wrap_cmd(id, command('cant write Dir', None))
        elif file is None:
            answer = wrap_cmd(id, command('file_not_found', None))
        else:
            success = change_file(fid, msg.data[1])
            answer = wrap_cmd(id, command('write', success))
            update_callbacks(fid , msg.src)
    return answer


def handle_connection(client_socket, client_address):
    logger.info(f'got connection from {client_address}')
    print('got connection from', client_address)
    msg = recv(client_socket)
    if type(msg) is kerberos_msg:
        handle_kerberos_setup(msg, client_socket)
    else:
        msg, id = handle_kerberos_wrap(msg)
        print(f'msg after wrap {msg}')
        logger.info(f'msg after wrap {msg}')
        if not msg is None:
            if 'fetch' == msg.cmd: # fix this written bad
                answer = handle_fetch_cmd(msg, id)
                send(client_socket, answer)
            elif 'write' == msg.cmd:
                answer = handle_write_cmd(msg, id)
                send(client_socket, answer)
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


def update_callbacks(fid, src = None):
    for addr in CALLBACK_TABLE.get(fid, None):
        if addr == src:
            continue
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(addr)
        send(s, wrap_cmd(IDSOCK_TABLE[addr],callback_message(fid)))
        s.close()


def print_table():
    for i, j in FILES_TABLE.items():
        print(i, j)


def main():
    """
        Main function to open a socket and wait for clients.

        :return: None
        """
    FORMAT = '%(asctime)s %(filename)s: %(message)s'
    logging.basicConfig(filename='VolumeServer.log', level=logging.INFO, format=FORMAT)
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
        server_down()
        server_socket.close()
    

if __name__ == "__main__":
    # Call the main handler function
    #set_table() 
    command.user = 'volume_server'
    load_table()
    print_table()
    #save_table()
    #set_files()
    main()