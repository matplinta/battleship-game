import socket
import argparse
from player import Player

class Server(Player):
    def __init__(self, host='127.0.0.1', port=9009):
        super(Server, self).__init__(host=host, port=port)
        self.connect()
        self.your_turn = False

    def connect(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)

        # add server socket object to the list of readable connections

        print(f"Battleship server started on {self.host}:{self.port}")
        self.conn_socket, addr = self.server_socket.accept()
        print(f"Client: {addr} connected")
        print("Wait for your opponent to initiate their's ships.")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-s', '--server', type=str, default="127.0.0.1", help='IP of the server')
    parser.add_argument('-p', '--port', type=int, default=9009, help='port used for the connection')
    args = parser.parse_args()

    instance = Server(host=args.server, port=args.port)
    try:
        instance.run()
    except KeyboardInterrupt:
        print("Ctrl+C entered, closing server...")
        instance.conn_socket.close()
        instance.server_socket.close()
