import sys
import socket
import select
import board

RECV_BUFFER = 4096

class Player():
    def __init__(self, host='127.0.0.1', port=9009):
        self.host = host
        self.port = port
        self.conn_socket = None
        self.your_turn = None


    def display_prompt(self, actor="Me"):
        print(f'\r[{actor}] ', end="")

    
    def send_message(self, message):
        if self.conn_socket:
            self.conn_socket.send((f"{message}\n").encode("utf-8"))


    def initialize_game(self):
        self.opponent_board = board.Board()
        self.local_board = board.Board()
        self.last_guess_stack = list()
        print("Initialize your board. You can either do it manually or use a random generator.")
        should_random = input("Do you wish to generate ships coordinates randomly? [Y/n] ")
        command = "random" if should_random.lower().startswith("y") else None
        self.local_board.init_ships(command)
        self.send_message("ready")
        print("Wait for your opponent to initiate their ships...")

        self.display_prompt()

    
    def get_data_from_opponent(self, endpoint: socket.socket):
        data = endpoint.recv(RECV_BUFFER)
        if not data:
            print('\nDisconnected from server')
            exit(1)
        data_decoded = data.decode("utf-8")[0:-1]
        print(f"\r[Opponent] {data_decoded}")
        return data_decoded


    def handle_received_msg(self, msg):
        msg = msg.lower()
        if msg == "hit":
            self.opponent_board.insert_by_coor(self.last_guess_stack.pop(), board.HIT_SYMBOL)
            self.your_turn = True
            print("[Me] My turn again!")

        elif msg == "missed":
            self.opponent_board.insert_by_coor(self.last_guess_stack.pop(), board.MISSED_SYMBOL)

        elif msg == "gameover":
            print("You WON!")
            exit(0)

        elif msg == "ready":
            print("Write your guess coordinates to start the game:")

        else:
            if self.local_board.is_hit(msg):
                print("[Me] Hit!")
                self.send_message("hit")
                if self.local_board.count_symbols(board.SHIP_SYMBOL) == 0:
                    print("Game over, You LOST!")
                    self.send_message("gameover")

            else:
                print("[Me] Missed!")
                self.send_message("missed")
                print("--->Your turn!")
                self.your_turn = True
        self.display_prompt()


    def handle_user_action(self, action):
        action = str(action).strip()
        if action == "player":
            self.local_board.print()

        elif action == "opponent":
            self.opponent_board.print()

        else:
            try:
                self.opponent_board.check_single_coor(action)
            except board.CoordinatesValueException as e: 
                print(str(e))
            else:
                if self.your_turn:
                    self.send_message(action)
                    self.last_guess_stack.append(action)
                    self.your_turn = False
                else:
                    print("Wait for your turn!")

        self.display_prompt()


    def run(self):
        self.initialize_game()
        while True:
            socket_list = [sys.stdin, self.conn_socket]
            # get the list sockets which are readable
            ready_to_read, ready_to_write, in_error = select.select(socket_list, [], [])

            for sock in ready_to_read:
                if sock == self.conn_socket:
                    msg = self.get_data_from_opponent(sock)
                    self.handle_received_msg(msg)

                else:  
                    user_action = sys.stdin.readline()
                    self.handle_user_action(user_action)
    