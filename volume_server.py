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
    """
    load_table()

    Parameters:
        None

    Returns:
        None

    Description:
        Loads the FILES_TABLE data structure from the file 'server.txt'.
    """
    global FILES_TABLE
    f = open('./server.txt', 'rb')
    FILES_TABLE = pickle.load(f)
    f.close()

def save_table():
    """
    save_table()

    Parameters:
        None

    Returns:
        None

    Description:
        Saves the current FILES_TABLE data structure to the file 'server.txt'.
    """
    f = open('./server.txt', 'wb')
    pickle.dump(FILES_TABLE, f)
    f.close()
    

def callback_message(fid):
    """
    callback_message()

    Parameters:
        fid: str
            The file ID for which to build a callback_broke command.

    Returns:
        Command
            A command object of type 'callback_broke' for the given fid.

    Description:
        Constructs and returns a 'callback_broke' command object for the specified file ID.
    """
    return command('callback_broke', fid)


def server_down_message():
    
    return command('server_down', None)


def get_file(fid):
    """
    get_file()

    Parameters:
        fid: str
            The file ID of the desired file in FILES_TABLE.

    Returns:
        AfsNode or None
            The AfsNode object corresponding to the fid from FILES_TABLE, or None if not found.

    Description:
        Retrieves the AfsNode object for the given fid from FILES_TABLE.
    """
    logger.info(f'getting file: { FILES_TABLE.get(fid, None)}')
    return FILES_TABLE.get(fid, None)


def change_file(fid, data):
    """
    change_file()

    Parameters:
        fid: str
            The file ID of the file to modify.
        data: bytes
            The new binary content to write to the file.

    Returns:
        bool
            True if the file was successfully updated; False if the target is a directory or an error occurred.

    Description:
        Updates the contents of an existing AfsFile by writing the new binary data to the actual file.
    """
    file = get_file(fid)
    if not type(file) is AfsFile:
        logger.error('cant change dir')
        return False
    with open(file.data, 'wb') as file:
        file.write(data)
    return True

def set_files():
    """
    set_files()

    Parameters:
        None

    Returns:
        None

    Description:
        Creates example text files inside the 'volume_server_files' directory with basic content.
    """
    for i in range(10):
        f = open(f'./volume_server_files/test{i}.txt', 'w')
        f.write(f'hello world {i}')
        f.close()

def set_table():
    """
    set_table()

    Parameters:
        None

    Returns:
        None

    Description:
        Builds an initial AfsDir/AfsFile tree structure, sets permissions, and populates FILES_TABLE.
    """
    dir = AfsDir('main dir', '1-1')
    add_to_table(dir)
    dir.add_write_access('rugh1')
    for i in range(1, 4):
        test = AfsFile(f'test{i}.txt', f'1-{i+1}', f'./volume_server_files/test{i}.txt')
        test.add_read_access('rugh1')
        add_to_table(test)
        dir.add(test)
    
    test = AfsFile('test4.txt', f'1-{5}', f'./volume_server_files/test4.txt')
    add_to_table(test)
    dir.add(test)
    
    dir2 = AfsDir('dir2', '1-123')
    dir2.add_read_access('rugh1')
    add_to_table(dir2)
    dir.add(dir2)
    for i in range(5, 10):
        test = AfsFile(f'test{i}.txt', f'1-{i+1}', f'./volume_server_files/test{i}.txt')
        test.add_write_access('rugh1')
        add_to_table(test)
        dir2.add(test)


def add_to_table(file:AfsNode):
    """
    add_to_table()

    Parameters:
        file: AfsNode
            An AfsNode object (AfsDir or AfsFile) to add to FILES_TABLE.

    Returns:
        None

    Description:
        Inserts the given AfsNode into FILES_TABLE using file.fid as the key.
    """

    FILES_TABLE[file.fid] = file


def handle_kerberos_setup(msg:kerberos_msg, client_socket):
    """
    handle_kerberos_setup()

    Parameters:
        msg: kerberos_msg
            A Kerberos ID-REQ message from the client.
        client_socket: socket.socket
            The socket object connected to the client.

    Returns:
        None

    Description:
        Performs the initial Kerberos authentication (ID-REQ), assigns a unique client_id,
        and updates the ID_TABLE.
    """
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
    """
    handle_kerberos_wrap()

    Parameters:
        msg: kerberos_wrap
            An encrypted Kerberos-wrapped message.

    Returns:
        tuple(Command, int) or None
            If the message is valid, returns a tuple containing the decrypted Command object and client_id;
            otherwise, returns None.

    Description:
        Decrypts the kerberos_wrap message, verifies that the client_id exists and matches, and returns
        the internal Command object. Returns None if verification fails.
    """
    id = msg.id
    print(id)
    user, key = ID_TABLE.get(id, (None,None))
    print(user, key)
    if key == None:
        print('unknown id')
        return None
    data = msg.get_msg(key)
    if not type(data) is command:
        print(f'idk type(data)= {type(data)}')
        return None
    if user != data.sender:
        print(f'user dont match {user} / {data.sender}')
        return None
    return  data, id


def get_rand_id():
        """
    get_rand_id()

    Parameters:
        None

    Returns:
        int
            A unique client identifier not currently in use in ID_TABLE.

    Description:
        Generates a random integer within the valid range that is not already present in ID_TABLE.
    """
        rand = random.randint(ID_MIN,ID_MAX)
        while rand in ID_TABLE.keys():
            rand = random.randint(ID_MIN, ID_MAX)
        return rand

def wrap_cmd(id, cmd):
    """
    wrap_cmd()

    Parameters:
        id: int
            An existing client identifier.
        cmd: Command
            The Command object to wrap.

    Returns:
        kerberos_wrap
            A Kerberos-wrapped message containing the command, encrypted with the key for the given client_id.

    Description:
        Wraps the provided Command object using Kerberos for the specified client_id and returns the wrapped message.
    """
    logger.info(f'wrapping id: {id} data {cmd} ')
    return kerberos_wrap(id, cmd, ID_TABLE[id][1])


def get_file_data(file:AfsFile):
    """
    get_file_data()

    Parameters:
        file: AfsFile
            An AfsFile object containing a file.data field that holds the path to the physical file.

    Returns:
        bytes
            The binary content of the physical file represented by the AfsFile.

    Description:
        Reads and returns the binary data from the physical file path stored in file.data.
    """
    f = open(file.data, 'rb')
    file_data = f.read()
    f.close()
    return file_data

def check_user_read_access(file, user):
    """
    check_user_read_access()

    Parameters:
        file: AfsNode
            An AfsNode object (file or directory) containing a list attribute raccess.
        user: str
            The username to check read access for.

    Returns:
        bool
            True if the user exists in file.raccess; otherwise False.

    Description:
        Checks whether the specified user has read permission for the given file or directory.
    """
    return user in file.read_access_list

def check_user_write_access(file, user):
    """
    check_user_write_access()

    Parameters:
        file: AfsNode
            An AfsNode object (file or directory) containing a list attribute waccess.
        user: str
            The username to check write access for.

    Returns:
        bool
            True if the user exists in file.waccess; otherwise False.

    Description:
        Checks whether the specified user has write permission for the given file or directory.
    """
    return user in file.write_access_list

def get_user_from_id(id):
    """
    get_user_from_id()

    Parameters:
        id: int
            An existing client identifier.

    Returns:
        str
            The username associated with the given client_id from ID_TABLE.

    Description:
        Retrieves the username mapped to the specified client_id from ID_TABLE.
    """
    return ID_TABLE[id][0] 

def handle_fetch_cmd(msg, id):
    """
    handle_fetch_cmd()

    Parameters:
        msg: Command
            A 'fetch' Command object with msg.data set to the fid of the file to fetch.
        id: int
            The client identifier of the requesting client.

    Returns:
        kerberos_wrap
            A Kerberos-wrapped response containing either the requested file data or 'file_not_found'.

    Description:
        Verifies that the client is authorized to read the specified fid, retrieves the object from FILES_TABLE,
        serializes it (e.g., pickle), updates CALLBACK_TABLE, and returns a Kerberos-wrapped response.
    """
    logger.info(f'fetch {msg}')
    if msg.data is None:
        return wrap_cmd(id, command('file_not_found', None))
       
    fid = msg.data
    file = get_file(fid)
    if file is None or not check_user_read_access(file, get_user_from_id(id)): #need change
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
    """
    handle_write_cmd()

    Parameters:
        msg: Command
            A 'write' Command object with msg.data set to (fid, data).
        id: int
            The client identifier of the requesting client.

    Returns:
        kerberos_wrap
            A Kerberos-wrapped response containing either a write-success or failure message, or an error.

    Description:
        Verifies that the client is authorized to write to the specified fid, extracts data from msg.data,
        updates the cached file, and sends callback notifications to other clients.
    """
    logger.info(f'fetch {msg}')
    if msg.data is None :
        answer = wrap_cmd(id, command('file_not_found', None))
    else:
        if len(msg.data) != 2:
            logger.error(f'data in write wasnt right {msg.data}')
            answer = wrap_cmd(id, command('error in data', None))
            return answer
        
        fid = msg.data[0]
        file = get_file(fid)
        if file is None:
            answer = wrap_cmd(id, command('file_not_found', None))
        elif check_user_read_access(file, get_user_from_id):
            answer = wrap_cmd(id, command('file_not_found', None))
        elif not check_user_write_access(file, get_user_from_id(id)):
            answer = wrap_cmd(id, command('dont have write accsess',None))
            
        elif type(file) is AfsDir:
            answer = wrap_cmd(id, command('cant write Dir', None))
        
        else:
            success = change_file(fid, msg.data[1])
            answer = wrap_cmd(id, command('write', success))
            update_callbacks(fid , msg.src)
    return answer


def handle_connection(client_socket, client_address):
    """
    handle_connection()

    Parameters:
        client_socket: socket.socket
            The socket object connected to the client.
        client_address: tuple
            A (IP, PORT) tuple representing the address of the client.

    Returns:
        None

    Description:
        Receives an initial message from the client (either kerberos_msg or kerberos_wrap),
        processes it accordingly (setup or decryption), and sends the appropriate response.
    """
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
    """
    update_callbacks()

    Parameters:
        fid: str
            The file ID for which a change has occurred.
        src: tuple or None
            The (IP, PORT) address of the sender that should not receive a callback; optional.

    Returns:
        None

    Description:
        Sends a 'callback_broke' wrapped message to all addresses in CALLBACK_TABLE[fid], excluding src.
    """
    for addr in CALLBACK_TABLE.get(fid, None):
        if addr == src:
            continue
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(addr)
        send(s, wrap_cmd(IDSOCK_TABLE[addr],callback_message(fid)))
        s.close()


def print_table():
    """
    print_table()

    Parameters:
        None

    Returns:
        None

    Description:
        Prints the contents of FILES_TABLE (mapping from fid to AfsNode) to the console.
    """
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
    # set_table()
    command.user = 'volume_server'
    load_table()
    print_table()
    # save_table()
    # set_files()
    main()