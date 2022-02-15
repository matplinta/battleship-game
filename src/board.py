import syslog
import random
from prettytable import PrettyTable

EMPTY_SPACE = "_"
SHIP_SYMBOL = "o"
HIT_SYMBOL = "X"
MISSED_SYMBOL = "M"
Y_COORDINATES = ["A","B","C","D","E","F","G","H","I","J"] 
X_COORDINATES = range(1, 11)


def row_array(symbol):
    return [symbol] + 10 * [EMPTY_SPACE]

def board_array():
    return [] + [row_array(elem) for elem in Y_COORDINATES]

def bipolarRange(start, stop):
    if start < stop:
        return range(start, stop + 1)
    elif start > stop:
        return range(stop, start + 1)
    else:
        return None


class Board:
    coor_mapping = {y: x for y, x in zip(Y_COORDINATES, X_COORDINATES)}
    reverse_coor_mapping = lambda idx: list(Board.coor_mapping.keys())[list(Board.coor_mapping.values()).index(idx)]
    def __init__(self):
        field_names_row = [" "] + [str(name) for name in X_COORDINATES]
        self.board = PrettyTable(field_names=field_names_row, hrules = 0)
        self.table = board_array()
        self.fill(self.table)
        self.yourTurn = True


    def print(self):
        print(self.board)


    def log_boardstate_to_syslog(self):
        lines = self.board.get_string().split("\n")
        for line in lines:
            syslog.syslog(syslog.LOG_INFO, lines)


    def fill(self, table):
        """Fill the table representing the board
        """
        for row in table:
            # print(list(Board.coor_mapping.keys())[list(Board.coor_mapping.values()).index(0)])
            self.board.add_row(row)


    def insert(self, row, col, symbol=SHIP_SYMBOL):
        """Insert single character into the board with the given bearing(row, col)
        """
        self.board.clear_rows()
        self.table[row-1][col] = symbol if len(symbol) == 1 else symbol[0]
        self.fill(self.table)
        return True


    def insert_by_coor(self, coordinates, symbol=SHIP_SYMBOL):
        """Insert single character into the board with the given string
        """
        row, col = self.get_single_coor(coordinates)
        self.insert(row, col, symbol)


    def get_single_coor(self, coordinates):
        """Get numerical representation of coordinates from a string
        """
        y_input = coordinates[0].upper()
        x_input = coordinates[1] if len(coordinates) == 2 else coordinates[1:3]

        coor_row = Board.coor_mapping[y_input]
        coor_col = int(x_input)
        return coor_row, coor_col


    def get_double_coor(self, coordinates):
        """Get numerical representation of coordinates from a string containing two coordinates
        """
        start, end = coordinates.split(" ")
        start_row, start_col = self.get_single_coor(start)
        end_row, end_col = self.get_single_coor(end)
        return start_row, start_col, end_row, end_col


    def check_single_coor(self, coordinates):
        """Check validity of coordinates
        """
        out_of_bounds_msg = "Values out of bounds! Try range from: [A-J][1-10]"
        if 2 <= len(coordinates) <= 3:
            y_input = coordinates[0].upper()
            x_input = coordinates[1] if len(coordinates) == 2 else coordinates[1:3]
            if y_input not in Board.coor_mapping:
                print(out_of_bounds_msg)
                return False
            coor_row = Board.coor_mapping[y_input]
            coor_col = int(x_input)
            if (coor_row < 1 or coor_row > 10) or (coor_col < 1 or coor_col > 10):
                print(out_of_bounds_msg)
                return False
            return True
        else:
            print("Too much input data! Try range from: [A-J][1-10]")
            return False
        

    def check_coordinates_validity(self, coordinates):
        """Check validity of a single or double coordinates
        """
        if 2 <= len(coordinates) <= 3:
            return self.check_single_coor(coordinates)
        else:
            if len(coordinates.split(" ")) != 2:
                print("Wrong coordinates format(or length)!")
                return False
            start, end = coordinates.split(" ")
            if not self.check_single_coor(start):
                print("Wrong ending coordinates!")
                return False
            start_row, start_col = self.get_single_coor(start)
            if not self.check_single_coor(end):
                print("Wrong ending coordinates!")
                return False
            end_row, end_col = self.get_single_coor(end)
            if (start_row != end_row and start_col != end_col):
                print("Wrong coordinates!")
                return False

            return True

    def check_point_availability(self, row, col):
        """check for any existing neighbouring points on a board
        """
        X = Y = 10
        neighbours = lambda x, y : [(x2, y2) for x2 in range(x-1, x+2)
                                             for y2 in range(y-1, y+2)
                                                if (0 < x <= X and
                                                    0 < y <= Y and
                                               # (x != x2 or y != y2) and
                                                    (1 <= x2 <= X) and
                                                    (1 <= y2 <= Y))]
        # print(neighbours(row,col))
        for coor_tuple in neighbours(row,col):
            if self.table[coor_tuple[0]-1][coor_tuple[1]] != EMPTY_SPACE:
                return False
        return True

    def checkShipAvailability(self, coorList, length):
        start_row, start_col, end_row, end_col = coorList
        if start_row == end_row:
            if len(bipolarRange(start_col, end_col)) != length:
                print("Wrong ship length!")
                return False
            for i in bipolarRange(start_col, end_col):
                if not self.check_point_availability(start_row, i):
                    print("Too close to the next ship! Try somewhere else.")
                    return False
        else:
            if len(bipolarRange(start_row, end_row)) != length:
                print("Wrong ship length!")
                return False
            for i in bipolarRange(start_row, end_row):
                if not self.check_point_availability(i, start_col):
                    print("Too close to the next ship! Try somewhere else.")
                    return False
        return True



    def insertShip(self, coorList, length):  # inserts Ship unconditionally
        start_row, start_col, end_row, end_col = coorList
        if start_row == end_row:
            if len(bipolarRange(start_col, end_col)) != length:
                print("Wrong ship length!")
                return False
            for i in bipolarRange(start_col, end_col):
                self.insert(start_row, i)
            return True
        else:
            if len(bipolarRange(start_row, end_row)) != length:
                print("Wrong ship length!")
                return False
            for i in bipolarRange(start_row, end_row):
                self.insert(i, start_col)
            return True

    def safeInsertShip(self, coordinates, length):              #inserts Ship with all precautions
        if not self.check_coordinates_validity(coordinates):
            return False
        if length == 1 and (len(coordinates) == 2 or len(coordinates) == 3):
            row, col = self.get_single_coor(coordinates)
            if self.check_point_availability(row, col):
                self.insert(row,col)
                return True
            else:
                print("Too close to the next ship! Try somewhere else.")
                return False
        elif length == 1 and not(len(coordinates) == 2 or len(coordinates) == 3):
            print("Wrong coordinates format!")
            return False
        elif length != 1 and (len(coordinates) == 2 or len(coordinates) == 3):
            print("Wrong coordinates format!")
            return False
        else:
            if self.checkShipAvailability(self.get_double_coor(coordinates), length):
                self.insertShip(self.get_double_coor(coordinates), length)
                return True
            else:
                return False


    def randomShipCoor(self, shipLength):
        while True:
            xPosition = random.randint(1, 10)
            yPosition = random.randint(1, 10)
            coor = list()
            if shipLength == 1:
                if self.check_point_availability(yPosition, xPosition):
                    strCoor = "{}{}".format(Board.reverse_coor_mapping(yPosition), xPosition)
                    break
            else:
                direction = random.randint(0, 3)
                if direction == 0:
                    thirdPosition = yPosition - (shipLength - 1)
                    if  thirdPosition < 1:
                        continue
                    else:
                        coor = [thirdPosition, xPosition, yPosition, xPosition]
                elif direction == 2:
                    thirdPosition = yPosition + (shipLength - 1)
                    if  thirdPosition > 10:
                        continue
                    else:
                        coor = [yPosition, xPosition, thirdPosition, xPosition]

                elif direction == 1:
                    thirdPosition = xPosition + (shipLength - 1)
                    if  thirdPosition > 10:
                        continue
                    else:
                        coor = [yPosition, xPosition, yPosition, thirdPosition]
                elif direction == 1:
                    thirdPosition = xPosition - (shipLength - 1)
                    if thirdPosition < 1:
                        continue
                    else:
                        coor = [yPosition, thirdPosition, yPosition, xPosition]
                if coor:
                    if self.checkShipAvailability( coor, shipLength):
                        strCoor = "{}{} {}{}".format(Board.reverse_coor_mapping(coor[0]), coor[1], Board.reverse_coor_mapping(coor[2]),coor[3])
                        break
                else:
                    continue

        print(strCoor)
        return strCoor

    def initShips(self, command = None):                                        #initiates loading ships sequence
        print("Initiate the position of your ships, in the following order:\n1x 4 square ship, 2x 3 square ship, 3x 2 square ship, 4x 1 square ship.",
              "Enter the starting and ending coordinates of the ship, like in the following example: A1 A4 for 4 square ship. ")
        shipList = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        if command == "ready":
            coorList = ["A1 A4", "C1 C3", "H10 J10", "A6 A7", "E2 F2", "G5 G6", "A10", "J1", "J5", "I3"]
            for i in range(10):
                self.safeInsertShip(coorList[i], shipList[i])
            return True
        elif command == "two":
            self.safeInsertShip("A2", 1)
            self.safeInsertShip("A4", 1)
            return True
        elif command == "short":
            for i in [2, 1]:

                print("Enter " + str(i) + " square ship coordinates: ")
                while(True):
                    coordinates = input()
                    if self.safeInsertShip(coordinates, i):
                        break
                self.print()
            return True
        elif command == "random":
            for shipLen in shipList:
                self.safeInsertShip(self.randomShipCoor(shipLen), shipLen)
        else:
            for i in shipList:
                print("Enter " + str(i) + " square ship coordinates: ")
                while(True):
                    coordinates = input()
                    if self.safeInsertShip(coordinates, i):
                        break
                self.print()
            return True

    def ifHit(self, coordinates):
        row, col = self.get_single_coor(coordinates)
        if self.table[row-1][col] == SHIP_SYMBOL:
            # print("[Me] Hit!")
            self.insert(row,col, HIT_SYMBOL)
            return True
        # print("[Me] Missed!")
        return False

    def countSymbols(self, symbol=SHIP_SYMBOL):
        count = 0
        for row in self.table:
            for elem in row:
                if elem == symbol:
                    count +=1
        # print("Game over, you WON!")
        return count


if __name__ == "__main__":
    Board().print()

