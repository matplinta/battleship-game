import sys
import socket
import argparse
from player import Player


def display_prompt(actor="Me"):
    print(f'\r[{actor}] ', end="")


class Client(Player):
    def __init__(self, host='127.0.0.1', port=9009):
        super(Client, self).__init__(host=host, port=port)
        self.connect()
        self.your_turn = True

    def connect(self):
        try:
            # get info about available interfaces, for TCP protocol
            socket_info = socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM, socket.SOL_TCP)            
        except Exception as e:
            print("getaddrinfo error: ", str(e))
            sys.exit(1)
        
        conn_id = None
        while conn_id is None:
            print("Choose one connection of the available ones:")
            # iterate from the back, as there are IPv4 interfaces
            for idx, interface in enumerate(reversed(socket_info)):
                family, type_, proto, canonname, sockaddr = interface
                print(f"[{idx}] {sockaddr}")
            try:
                choice = int(input())
            except ValueError:
                print("You need to enter the number")
                continue
            if 0 <= choice <= len(socket_info):
                conn_id = choice
                break

        family, type_, _, _, sockaddr = list(reversed(socket_info))[conn_id]
        self.conn_socket = socket.socket(family, type_)
        self.conn_socket.settimeout(2)
        try:
            self.conn_socket.connect(sockaddr)
        except ConnectionRefusedError as e:
            print(f"Connection to {sockaddr} is not available. Maybe server has not started yet?")
            sys.exit(1)
        else:
            print('Connected to remote host.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-s', '--server', type=str, default="127.0.0.1", help='IP of the server')
    parser.add_argument('-p', '--port', type=int, default=9009, help='port used for the connection')
    args = parser.parse_args()

    instance = Client(host=args.server, port=args.port)
    try:
        instance.run()
    except KeyboardInterrupt:
        print("Ctrl+C entered, closing connection.")
        instance.conn_socket.close()

