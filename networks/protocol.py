import pickle
from msg import command

def int_to_bytes(number: int) -> bytes:
    return number.to_bytes(length=(8 + (number + (number < 0)).bit_length()) // 8, byteorder='big', signed=True)

def int_from_bytes(binary_data: bytes) -> int:
    return int.from_bytes(binary_data, byteorder='big', signed=True)

def send(connected_socket, msg:object):
    """
    Send a message over the connected socket.

    :param connected_socket: The connected socket to send the message through.
    :type connected_socket: socket.socket

    :param msg: The message to be sent.
    :type msg: str

    :return: None
    :rtype: None
    """
    print(f'sending: {msg}')
    data = pickle.dumps(msg)
    # Check if the last character of the 'msg' string is a space
    # Convert the length of the 'msg' string to hexadecimal representation, excluding the '0x' prefix
    msg = int_to_bytes(len(data)) + b'!' + data
    print(msg)
    # Encode the modified 'msg' string and send it through the 'connected_socket'
    connected_socket.send(msg)


def recv(connected_socket):
    """
    Receive a message from the connected socket.

    :param connected_socket: The connected socket to receive the message from.
    :type connected_socket: socket.socket

    :return: A list containing the split components of the received message.
    :rtype: list[str]
    """
    # Receive the length of the message in hexadecimal
    print('reciving')
    length_hex = b''
    tmp = b''
    while tmp != b'!':
        print(length_hex)
        length_hex += tmp
        tmp = connected_socket.recv(1)

    # Convert the length to an integer
    length = int_from_bytes(length_hex)

    # Receive the message until the expected length is reached
    received_msg = b''
    while len(received_msg) < length:
        received_msg += connected_socket.recv(1)
    data = pickle.loads(received_msg)
    # Split the received message using '!' as the separator
    return data