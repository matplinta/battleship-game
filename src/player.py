import sys
import socket
import select
import board

RECV_BUFFER = 4096

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.
    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


class Player():
    def __init__(self, host='127.0.0.1', port=9009, log_method=print):
        self.host = host
        self.port = port
        self.conn_socket = None
        self.log = log_method
        self.your_turn = None


    def display_prompt(self, actor="Me"):
        print(f'\r[{actor}] ', end="")

    
    def send_message(self, message):
        if self.conn_socket:
            self.conn_socket.send((f"{message}\n").encode("utf-8"))


    def initialize_game(self, init_ships_method=None):
        self.opponent_board = board.Board()
        self.local_board = board.Board()
        self.last_guess_stack = list()
        if init_ships_method is None:
            print("Initialize your board. You can either do it manually or use a random generator.")
            should_random = query_yes_no("Do you wish to generate ships coordinates randomly?")
            command = "random" if should_random else None
        else:
            command = init_ships_method
        self.local_board.init_ships(command)
        self.send_message("ready")
        self.log("Wait for your opponent to initiate their ships...")
        self.display_prompt()

    
    def get_data_from_opponent(self, endpoint: socket.socket):
        data = endpoint.recv(RECV_BUFFER)
        if not data:
            self.log('\nDisconnected from server')
            exit(1)
        data_decoded = data.decode("utf-8")[0:-1]
        return data_decoded


    def handle_received_msg(self, msg):
        msg = msg.lower()
        if msg == "hit":
            self.opponent_board.insert_by_coor(self.last_guess_stack.pop(), board.HIT_SYMBOL)
            self.your_turn = True
            self.log("[Me] My turn again!")

        elif msg == "missed":
            self.opponent_board.insert_by_coor(self.last_guess_stack.pop(), board.MISSED_SYMBOL)

        elif msg == "gameover":
            self.log("You WON!")
            exit(0)

        elif msg == "ready":
            if self.your_turn:
                self.log("Write your guess coordinates to start the game:")
            else:
                self.log("Wait for opponent to start guessing...")

        else:
            if self.local_board.is_hit(msg):
                self.log("[Me] Hit!")
                self.send_message("hit")
                if self.local_board.count_symbols(board.SHIP_SYMBOL) == 0:
                    self.log("Game over, You LOST!")
                    self.send_message("gameover")

            else:
                self.log("[Me] Missed!")
                self.send_message("missed")
                self.log("--->Your turn!")
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
                self.log(str(e))
            else:
                if self.your_turn:
                    self.send_message(action)
                    self.last_guess_stack.append(action)
                    self.your_turn = False
                else:
                    self.log("Wait for your turn!")

        self.display_prompt()


    def run(self, init_ships_method=None):
        self.initialize_game(init_ships_method)
        while True:
            socket_list = [sys.stdin, self.conn_socket]
            # get the list sockets which are readable
            ready_to_read, ready_to_write, in_error = select.select(socket_list, [], [])

            for sock in ready_to_read:
                if sock == self.conn_socket:
                    msgs = self.get_data_from_opponent(sock)
                    for msg in msgs.strip().split("\n"):
                        self.log(f"\r[Opponent] {msg}")
                        self.handle_received_msg(msg)

                else:  
                    user_action = sys.stdin.readline()
                    self.handle_user_action(user_action)
    