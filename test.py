from kerberos.client import *


def main():
    cli = client_kerberos_socket('rugh1', ' hello')
    client_kerberos_socket.__class__
    print(cli)
    new_cli  = client_kerberos_socket()
    print(new_cli)

main()
