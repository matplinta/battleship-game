import sys
import socket
import board
import random
import syslog
import time
import os
import signal

RECV_BUFFER = 4096
MAXFD = 64
SLEEPTIME = 1

class Server():
    def __init__(self):
        port = int(sys.argv[1]) if len(sys.argv) == 2 else 9009
        try:
            serverInfo = socket.getaddrinfo(None, port, socket.AF_UNSPEC, socket.SOCK_STREAM, socket.SOL_TCP)           #obsluga DNS
        except Exception as e:
            print("getaddrinfo error: ", e)
            sys.exit()
        server_socket = None
        for interface in reversed(serverInfo):
            try:
                server_socket = socket.socket(interface[0], interface[1])                           #tworzenie socketu servera
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(interface[4])
                server_socket.listen(1)
                print(interface[0], interface[4])
                break
            except:
                server_socket.close()
                continue
        if not server_socket:
            print("Could not create server socket, exiting.")
            sys.exit()
        print("Battleship server started on port  " + str(port))
        self.lastGuessStack = list()  # stos przechowujacy ostatnie zgadywane polozenie
        self.guessStack = list()
        self.oponentBoard = board.Board()  # inicjalizacja planszy przeciwnika
        self.localBoard = board.Board()  # inicjalizacja planszy gracza

        # Start the daemon

        self.daemonize(1000, server_socket)
        self.run(server_socket)

    def daemonize(self, uid, noDelSock):                                #metoda do inicjalizacji demona
        """Deamonize class. UNIX double fork mechanism."""

        try:
            pid = os.fork()                                             #pierwszy fork, proces potonmy działa w tle,
            if pid > 0:                                                 #proces dziedziczy identyfikator grupy ale otrzymuje swój własny PID
                # exit first parent                                     #pewnosc, ze proces nie jest przywodca grupy procesow
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #1 failed: {0}\n'.format(err))
            sys.exit(1)

        # decouple from parent environment
        os.chdir('/')                                                   #zmiana katalogu roboczego

        os.setsid()                                                     #utworzenie nowej sesji, proces staje sie przywodca nowej grupy procesow, bez terminala sterujacego

        os.umask(0)                                                     #zerowanie maski trybu dostepu do tworzonych plikow

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

        # for i in range(3, MAXFD):
        #     tempfd = socket.socket(fileno=i)                          #nie trzeba! Since Python 3.4 file descriptors created by Python are non-inheritable by default!
        #     if noDelSock != tempfd:
        #         tempfd.close()
        #     else:
        #         print("ten file deskrpytor!")

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        os.setuid(uid)                                                  #zmiana właściciela procesu


     # DAEMON START
    def run(self, server_socket):
        syslog.openlog("Battleship server bot", syslog.LOG_PID, syslog.LOG_LOCAL7)              #daemon syslog

        self.client_socket, addr = server_socket.accept()                                       # akceptowanie polaczenia z klientem
        syslog.syslog(syslog.LOG_NOTICE, "Client " + str(addr) + " connected")
        self.localBoard.init_ships("random")                                                           #wpisanie polozenia statkow gracza
        self.client_socket.send(("Opponent ready!\n").encode("utf-8"))                               #wyslij wiadomosc gotowosci do przeciwnika
        self.localBoard.log_boardstate_to_syslog()
        syslog.syslog(syslog.LOG_INFO, "Wait for your opponent to initiate their's ships.")

        while True:
            # incoming message from remote server, s
            data = self.client_socket.recv(RECV_BUFFER)
            if not data:
                syslog.syslog(syslog.LOG_NOTICE, '\nDisconnected from server')
                sys.exit()
            else:                                                                                    # ODCZYT, obsluga odczytu wiadomosci
                # print data
                readableData = data.decode("utf-8")[0:-1]
                syslog.syslog(syslog.LOG_INFO, "[Opponent]" + data.decode("utf-8"))

                if readableData == "Hit!":
                    self.oponentBoard.insert_by_coor(self.lastGuessStack.pop(), board.HIT_SYMBOL)
                    self.localBoard.your_turn = True
                    syslog.syslog(syslog.LOG_INFO, "[Me] My turn again.")
                    time.sleep(SLEEPTIME)
                    syslog.syslog(syslog.LOG_INFO, "[Me] " + str(self.respond()))
                elif readableData == "Missed!":
                    self.oponentBoard.insert_by_coor(self.lastGuessStack.pop(), board.MISSED_SYMBOL)
                elif readableData == "Game over.":
                    syslog.syslog(syslog.LOG_INFO, "You WON!")
                    exit()
                elif readableData == "Opponent ready!":
                    syslog.syslog(syslog.LOG_INFO, "Write your guess coordinates to start the game.")
                    continue

                else:
                    if self.localBoard.is_hit(readableData):
                        syslog.syslog(syslog.LOG_INFO, "[Me] Hit!")
                        self.client_socket.send(("Hit!\n").encode("utf-8"))
                        if self.localBoard.count_symbols(board.SHIP_SYMBOL) == 0:
                            syslog.syslog(syslog.LOG_INFO, "End of game, You LOST!")
                            self.client_socket.send(("Game over.\n").encode("utf-8"))
                        continue
                    else:
                        syslog.syslog(syslog.LOG_INFO, "[Me] Missed!")
                        self.client_socket.send(("Missed!\n").encode("utf-8"))
                    syslog.syslog(syslog.LOG_INFO, "-->Your turn!")
                    self.localBoard.your_turn = True
                    time.sleep(SLEEPTIME)
                    syslog.syslog(syslog.LOG_INFO, "[Me] " + str(self.respond()))

        server_socket.close()

    def respond(self):
        while True:
            xPosition = random.randint(1, 10)
            yPosition = random.randint(1, 10)
            coor = board.Board.reverseDict(yPosition) + str(xPosition) + "\n"
            try:
                self.oponentBoard.check_single_coor(coor.rstrip())
            except board.CoordinatesValueException as e: 
                print(str(e))
            else:
                if coor not in self.guessStack:
                    break

        if self.localBoard.your_turn:
            self.client_socket.send(coor.encode("utf-8"))
            self.lastGuessStack.append(coor)  # w celu ustalenia kolejnosci
            self.guessStack.append((coor))
            self.localBoard.your_turn = False
        return coor

instance = Server()