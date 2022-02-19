import pytest
from src.board import Board
from src.board import SHIP_SYMBOL
from src.board import CoordinatesValueException, ShipLengthException, ShipNeighPointsNotAvailableException

def test_board_initialization():
    assert Board().board.get_string().split("\n") == ['+---+---+---+---+---+---+---+---+---+---+----+', 
                                                      '|   | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |', 
                                                      '+---+---+---+---+---+---+---+---+---+---+----+', 
                                                      '| A | _ | _ | _ | _ | _ | _ | _ | _ | _ | _  |', 
                                                      '| B | _ | _ | _ | _ | _ | _ | _ | _ | _ | _  |', 
                                                      '| C | _ | _ | _ | _ | _ | _ | _ | _ | _ | _  |', 
                                                      '| D | _ | _ | _ | _ | _ | _ | _ | _ | _ | _  |', 
                                                      '| E | _ | _ | _ | _ | _ | _ | _ | _ | _ | _  |', 
                                                      '| F | _ | _ | _ | _ | _ | _ | _ | _ | _ | _  |', 
                                                      '| G | _ | _ | _ | _ | _ | _ | _ | _ | _ | _  |', 
                                                      '| H | _ | _ | _ | _ | _ | _ | _ | _ | _ | _  |', 
                                                      '| I | _ | _ | _ | _ | _ | _ | _ | _ | _ | _  |', 
                                                      '| J | _ | _ | _ | _ | _ | _ | _ | _ | _ | _  |', 
                                                      '+---+---+---+---+---+---+---+---+---+---+----+']


def test_get_single_coor():
    y_axis = Board.y_coor_mapping.keys()
    x_axis = Board.y_coor_mapping.values()
    for y in y_axis:
        for x in x_axis:
            row, col = Board.get_single_coor(f"{y}{x}")
            assert row == Board.y_coor_mapping[y]
            assert col == x


def test_get_single_coor_out_of_bounds_y():
    with pytest.raises(KeyError):
        row, col = Board.get_single_coor("X10")


def test_get_single_coor_out_of_bounds_x():
    with pytest.raises(ValueError):
        row, col = Board.get_single_coor("A11")


def test_get_double_coor():
    start_row, start_col, end_row, end_col = Board.get_double_coor("A1 J10")
    assert start_row == 1
    assert start_col == 1
    assert end_row == 10
    assert end_col == 10


def test_insert_by_coor():
    board = Board()
    board.insert_by_coor("A1")


def test_check_single_coor():
    with pytest.raises(CoordinatesValueException):
        Board.check_single_coor("A11")

    y_axis = Board.y_coor_mapping.keys()
    x_axis = Board.y_coor_mapping.values()
    for y in y_axis:
        for x in x_axis:
            Board.check_single_coor(f"{y}{x}")


def test_check_double_coor():
    with pytest.raises(CoordinatesValueException):
        Board.check_double_coor("A1 A1")
    with pytest.raises(CoordinatesValueException):
        Board.check_double_coor("A1 B2")

    Board.check_double_coor("A1 A2")
    Board.check_double_coor("A1 B1")


def test_insert_by_coor():
    board = Board()
    board.insert_by_coor("C4")


def test_is_point_available():
    board = Board()
    board.insert_by_coor("C3")
    assert board.is_point_available(3, 4) is False
    assert board.is_point_available(2, 2) is False
    assert board.is_point_available(2, 3) is False
    assert board.is_point_available(2, 4) is False
    assert board.is_point_available(3, 2) is False
    assert board.is_point_available(3, 4) is False
    assert board.is_point_available(4, 2) is False
    assert board.is_point_available(4, 3) is False
    assert board.is_point_available(4, 4) is False
    assert board.is_point_available(1, 1) is True


def test_check_ship_length():
    board = Board()
    board.check_ship_length(1, 4, 4)
    with pytest.raises(ShipLengthException):
        board.check_ship_length(1, 4, 5)


def test_check_neighbouring_points():
    board = Board()
    board.check_neighbouring_points(1, 4, 3, ship_alignment="horizontal")
    board.check_neighbouring_points(1, 4, 3, ship_alignment="vertical")
    board.insert_by_coor("C3")
    with pytest.raises(ShipNeighPointsNotAvailableException):
        board.check_neighbouring_points(1, 4, 3, ship_alignment="horizontal")
    with pytest.raises(ShipNeighPointsNotAvailableException):
        board.check_neighbouring_points(1, 4, 3, ship_alignment="vertical")
    with pytest.raises(ValueError):
        board.check_neighbouring_points(1, 4, 3, ship_alignment="xxx")


def test_is_ship_available():
    board = Board()
    status, exception =  board.is_ship_available((3, 1, 3, 4), 4)
    assert status is True
    assert exception is None
    board.insert_by_coor("C3")
    status, exception =  board.is_ship_available((3, 1, 3, 4), 4)
    assert status is False
    assert isinstance(exception, ShipNeighPointsNotAvailableException)
    status, exception =  board.is_ship_available((3, 1, 3, 4), 2)
    assert status is False
    assert isinstance(exception, ShipLengthException)