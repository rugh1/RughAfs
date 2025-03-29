import socket
from threading import Thread
import pickle
from AfsFile import AfsFile, AfsDir, AfsNode
from protocol import send, recv
from msg import command
QUEUE_SIZE = 10
IP = '127.0.0.1'
PORT = 22353

FILES_TABLE = {}
CALLBACK_TABLE = {}


def load_table():
    global FILES_TABLE
    f = open('./server.txt', 'rb')
    FILES_TABLE = pickle.load(f)
    f.close()

def save_table():
    f = open('./server.txt', 'wb')
    pickle.dump(FILES_TABLE, f)
    f.close()
    
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

def handle_connection(client_socket, client_address):
    a = recv(client_socket)
    print(a)
    if 'fetch' == a.cmd: # fix this written bad
        fid = int(a.data)
        file = get_file(fid)
        if file is None:
            answer = command('file not found', None)
        else:
            answer = command('file', file.pickle_me())
            if(CALLBACK_TABLE.get(fid, 'def') == 'def'):
                CALLBACK_TABLE[fid] = []
            CALLBACK_TABLE[fid].append(client_socket)
        send(client_socket, answer)

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
        server_socket.close()


if __name__ == "__main__":
    # Call the main handler function
    # set_table()
    load_table()
    print_table()
    # print(get_file(1))

    main()