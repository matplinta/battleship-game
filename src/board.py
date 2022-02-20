import syslog
import random
from prettytable import PrettyTable

EMPTY_SPACE = "_"
SHIP_SYMBOL = "o"
HIT_SYMBOL = "X"
MISSED_SYMBOL = "M"
Y_COORDINATES = ["A","B","C","D","E","F","G","H","I","J"] 
X_COORDINATES = range(1, 11)


class BoardBaseException(Exception):
    """Class exception for coordinates value error"""
    pass


class CoordinatesValueException(BoardBaseException):
    """Class exception for coordinates value error"""
    pass


class ShipLengthException(BoardBaseException):
    """Exception indicating that ship lenght is incorrect"""
    pass


class ShipNeighPointsNotAvailableException(BoardBaseException):
    """Exception indicating that ship neighbouring points are not available"""
    pass


def row_array(symbol):
    return [symbol] + 10 * [EMPTY_SPACE]

def board_array():
    return [] + [row_array(elem) for elem in Y_COORDINATES]


class Board:
    y_coor_mapping = {y: x for y, x in zip(Y_COORDINATES, range(1, 11))}
    reverse_coor_mapping = lambda idx: list(Board.y_coor_mapping.keys())[list(Board.y_coor_mapping.values()).index(idx)]

    def __init__(self):
        field_names_row = [" "] + [str(name) for name in X_COORDINATES]
        self.board = PrettyTable(field_names=field_names_row, hrules = 0)
        self.table = board_array()
        self.fill(self.table)


    @staticmethod
    def ship_range(start, stop):
        if start <= stop:
            return range(start, stop + 1)
        else:
            return range(stop, start + 1)


    @staticmethod
    def get_single_coor(coordinates):
        """Get numerical representation of coordinates from a string
        """
        y_input = coordinates[0].upper()
        x_input = coordinates[1] if len(coordinates) == 2 else coordinates[1:3]

        coor_row = Board.y_coor_mapping[y_input]
        if int(x_input) not in X_COORDINATES:
            raise ValueError()
        else:
            coor_col = int(x_input)
        return coor_row, coor_col


    @staticmethod
    def get_double_coor(coordinates):
        """Get numerical representation of coordinates from a string containing two coordinates
        """
        start, end = coordinates.split(" ")
        start_row, start_col = Board.get_single_coor(start)
        end_row, end_col = Board.get_single_coor(end)
        return start_row, start_col, end_row, end_col


    @staticmethod
    def check_single_coor(coordinates):
        """Check that single coordinates are valid
        """
        out_of_bounds_msg = "Values out of bounds! Try range from: [A-J][1-10]"
        if 2 <= len(coordinates) <= 3:
            y_input = coordinates[0].upper()
            x_input = coordinates[1] if len(coordinates) == 2 else coordinates[1:3]
            if y_input not in Board.y_coor_mapping:
                raise CoordinatesValueException(out_of_bounds_msg)
            coor_row = Board.y_coor_mapping[y_input]
            coor_col = int(x_input)
            if (coor_row < 1 or coor_row > 10) or (coor_col < 1 or coor_col > 10):
                raise CoordinatesValueException(out_of_bounds_msg)
        else:
            raise CoordinatesValueException("Too much input data! Try range from: [A-J][1-10]")


    @staticmethod
    def check_double_coor(coordinates):
        """Check validity of double coordinates. Coordinates must have a common row or 
           a common column, but not both, so that ships are not aligned diagonally. 
           Also starting and ending cooridnates shall not be identical. 
           Throws CoordinatesValueException if the aforementioned requirements are not met.  
        """
        if len(coordinates.split(" ")) != 2:
            raise CoordinatesValueException("Wrong coordinates format(or length)!")
        start, end = coordinates.split(" ")
        try:
            Board.check_single_coor(start)
        except CoordinatesValueException as e:
            raise CoordinatesValueException(f"Wrong starting coordinates: {str(e)}")
        try:
            Board.check_single_coor(end)
        except CoordinatesValueException as e:
            raise CoordinatesValueException(f"Wrong ending coordinates: {str(e)}")
        start_row, start_col = Board.get_single_coor(start)
        end_row, end_col = Board.get_single_coor(end)
        if (start_row != end_row and start_col != end_col):
            raise CoordinatesValueException(f"Coordinates cannot go diagonally")


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
            # print(list(Board.y_coor_mapping.keys())[list(Board.y_coor_mapping.values()).index(0)])
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
        row, col = Board.get_single_coor(coordinates)
        self.insert(row, col, symbol)


    def is_point_available(self, row, col):
        """Checks if every neighbouring point relative to the specified by the arguments is free on the board.
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


    def check_ship_length(self, start, end, length):
        if len(Board.ship_range(start, end)) != length:
            raise ShipLengthException("Wrong ship length!")


    def check_neighbouring_points(self, start, end, starting_point_in_axis, ship_alignment="horizontal"):
        if ship_alignment not in ["horizontal", "vertical"]:
            raise ValueError(f"Ship alignemnt: {ship_alignment} not supported")
        for i in Board.ship_range(start, end):
            coor_order = (starting_point_in_axis, i) if ship_alignment == "horizontal" else (i, starting_point_in_axis)
            if not self.is_point_available(*coor_order):
                raise ShipNeighPointsNotAvailableException("Too close to the next ship! Try somewhere else.")


    def is_ship_available(self, coor_list, length):
        """Checks if ship with specified length can be placed on the board. 
           Looks for neighbouring points is all are available, as ships cannot touch each other.
           Returns boolean indicating if ship placement in the specified coordinates is available.
        """
        start_row, start_col, end_row, end_col = coor_list
        try:
            if start_row == end_row:
                self.check_ship_length(start_col, end_col, length)
                self.check_neighbouring_points(start_col, end_col, start_row, "horizontal")
            else:
                self.check_ship_length(start_row, end_row, length)
                self.check_neighbouring_points(start_row, end_row, start_col, "vertical")
        except BoardBaseException as exception:
            return False, exception
        else:
            return True, None


    def insert_ship(self, coor_list, length):
        """Inserts ship onto board without regard for other points
        """
        start_row, start_col, end_row, end_col = coor_list
        if start_row == end_row:
            self.check_ship_length(start_col, end_col, length)
            for i in Board.ship_range(start_col, end_col):
                self.insert(start_row, i)
        else:
            self.check_ship_length(start_row, end_row, length)
            for i in Board.ship_range(start_row, end_row):
                self.insert(i, start_col)


    def safe_insert_ship(self, coordinates, length):
        """Inserts ship if the length and neighbouring points are available  
        """
        coor_list = coordinates.split(" ")
        if len(coor_list) == 1:
            coordinates = f"{coor_list[0]} {coor_list[0]}"
        elif len(coor_list) != 2:
            print("Wrong coordinates format!")
            return False
        
        self.check_double_coor(coordinates)
        status, exception = self.is_ship_available(Board.get_double_coor(coordinates), length)
        if status is True:
            self.insert_ship(Board.get_double_coor(coordinates), length)
        else:
            print(str(exception))

        return status


    def random_ship_coor(self, ship_length):
        while True:
            x = random.randint(1, 10)
            y = random.randint(1, 10)
            coor = list()
            if ship_length == 1:
                if self.is_point_available(y, x):
                    coor_str = f"{Board.reverse_coor_mapping(y)}{x}"
                    break
            else:
                direction = random.randint(0, 3)
                if direction == 0:
                    z = y - (ship_length - 1)
                    if  z < 1:
                        continue
                    else:
                        coor = [z, x, y, x]
                elif direction == 2:
                    z = y + (ship_length - 1)
                    if  z > 10:
                        continue
                    else:
                        coor = [y, x, z, x]

                elif direction == 1:
                    z = x + (ship_length - 1)
                    if  z > 10:
                        continue
                    else:
                        coor = [y, x, y, z]
                elif direction == 3:
                    z = x - (ship_length - 1)
                    if z < 1:
                        continue
                    else:
                        coor = [y, z, y, x]
                if coor:
                    if self.is_ship_available(coor, ship_length):
                        coor_str = "{}{} {}{}".format(Board.reverse_coor_mapping(coor[0]), coor[1], 
                                                      Board.reverse_coor_mapping(coor[2]), coor[3])
                        break
                else:
                    continue

        return coor_str

    def init_ships(self, command=None): 
        """Initiates loading ships sequence
        """
        init_mgs = """Initiate the position of your ships in the following order:
- 1x 4 square ships, 
- 2x 3 square ships, 
- 3x 2 square ships, 
- 4x 1 square ships.
Enter the starting and ending coordinates of the ship, 
like so: "A1 A4" for a one 4-square ship.
"""
        print(init_mgs)
        shipList = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        if command == "ready":
            coor_list = ["A1 A4", "C1 C3", "H10 J10", "A6 A7", "E2 F2", "G5 G6", "A10", "J1", "J5", "I3"]
            for i in range(10):
                self.safe_insert_ship(coor_list[i], shipList[i])
            return True
        elif command == "two":
            self.safe_insert_ship("A2", 1)
            self.safe_insert_ship("A4", 1)
            return True
        elif command == "short":
            for i in [2, 1]:

                print("Enter " + str(i) + " square ship coordinates: ")
                while(True):
                    coordinates = input()
                    if self.safe_insert_ship(coordinates, i):
                        break
                self.print()
            return True
        elif command == "random":
            for shipLen in shipList:
                self.safe_insert_ship(self.random_ship_coor(shipLen), shipLen)
        else:
            for i in shipList:
                print("Enter " + str(i) + " square ship coordinates: ")
                while(True):
                    coordinates = input()
                    if self.safe_insert_ship(coordinates, i):
                        break
                self.print()
            return True


    def is_hit(self, coordinates):
        row, col = Board.get_single_coor(coordinates)
        if self.table[row-1][col] == SHIP_SYMBOL:
            self.insert(row, col, HIT_SYMBOL)
            return True
        return False


    def count_symbols(self, symbol=SHIP_SYMBOL):
        count = 0
        for row in self.table:
            for elem in row:
                if elem == symbol:
                    count +=1
        return count


if __name__ == "__main__":
    Board().print()

