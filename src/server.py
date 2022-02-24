import os
import sys
import signal
import socket
import syslog
import random
import argparse
from time import sleep
import board
from player import Player


class Server(Player):
    def __init__(self, host='127.0.0.1', port=9009, daemon=False):
        self.is_daemon = daemon
        log_method = syslog.syslog if self.is_daemon else print
        super(Server, self).__init__(host=host, port=port, log_method=log_method)
        
        if self.is_daemon:
            self.guess_list = board.Board.generate_all_fields_list()
            self.connect_daemon()
        else: 
            self.connect()
        self.your_turn = False


    def connect(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(1)

        # add server socket object to the list of readable connections

        self.log(f"Battleship server started on {self.host}:{self.port}")
        self.conn_socket, addr = self.server_socket.accept()
        self.log(f"Client: {addr} connected")


    def connect_daemon(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(1)

        # add server socket object to the list of readable connections
        
        print(f"Battleship server started on {self.host}:{self.port}")
        self.daemonize(1000)
        syslog.openlog("Battleship server bot", syslog.LOG_PID, syslog.LOG_LOCAL7)                                                #zmiana właściciela procesu
        self.conn_socket, addr = self.server_socket.accept()
        self.log(f"Client: {addr} connected")

    
    def daemonize(self, uid):
        """Daemonize process. UNIX double fork mechanism."""

        try:
            pid = os.fork()                                             #pierwszy fork, proces potonmy działa w tle,
            if pid > 0:                                                 #proces dziedziczy identyfikator grupy ale otrzymuje swój własny PID
                # exit first parent                                     #pewnosc, ze proces nie jest przywodca grupy procesow
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #1 failed: {0}\n'.format(err))
            sys.exit(1)

        # decouple from parent environment
        os.chdir('/')                     # zmiana katalogu roboczego
        os.setsid()                       # utworzenie nowej sesji, proces staje sie przywodca nowej grupy procesow, 
                                          # bez terminala sterujacego
        os.umask(0)                       # zerowanie maski trybu dostepu do tworzonych plikow

        signal.signal(signal.SIGHUP, signal.SIG_IGN)                    #ignorujemy sygnal SIGHUP, poniewaz jest on wysylany do potomkow po zamknieciu przywodcy sesji
        # do second fork
        try:
            pid = os.fork()                                             #zamykamy proces macierzysty; zapobiegamy automatycznegou uzyskaniu terminala sterujacego przez nasz proces
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #2 failed: {0}\n'.format(err))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        os.setuid(uid)
 

    def run_bot(self):
        self.initialize_game(init_ships_method="random")
        self.local_board.log_boardstate_to_syslog()
        while True:
            msg = self.get_data_from_opponent(self.conn_socket)
            self.handle_received_msg(msg)
            if self.your_turn is True:
                sleep(random.randint(1, 3))
                self.daemon_response()


    def daemon_response(self):
        guess_coor = random.choice(self.guess_list)
        self.log(f"Guess coordinates: {guess_coor}")
        self.send_message(guess_coor)
        self.last_guess_stack.append(guess_coor)
        self.guess_list.remove(guess_coor)
        self.your_turn = False
        return guess_coor


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-s', '--server', type=str, default="127.0.0.1", help='IP of the server')
    parser.add_argument('-p', '--port', type=int, default=9009, help='port used for the connection')
    parser.add_argument('-b', '--bot', action='store_true', help='Specify this option if you want to spawn a bot to play with')
    args = parser.parse_args()

    instance = Server(host=args.server, port=args.port, daemon=args.bot)
    try:
        if args.bot:
            instance.run_bot()
        else:
            instance.run()
    except KeyboardInterrupt:
        print("Ctrl+C entered, closing server...")
        instance.conn_socket.close()
        instance.server_socket.close()
    except Exception as e:
        instance.log(str(e))
        instance.conn_socket.close()
        instance.server_socket.close()
