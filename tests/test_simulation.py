import pytest

from src.simulation import Simulation


def test_cell_inside_map_is_not_blocked():
    sim = Simulation()
    assert sim.is_blocked((0, 0)) is False


def test_cell_outside_map_is_blocked():
    sim = Simulation()
    assert sim.is_blocked((20, 20)) is True
    assert sim.is_blocked((-1, 0)) is True


def test_added_obstacle_is_blocked():
    sim = Simulation()
    sim.add_obstacle((4, 4))
    assert sim.is_blocked((4, 4)) is True


def test_removed_obstacle_is_free():
    sim = Simulation()
    sim.add_obstacle((4, 4))
    sim.remove_obstacle((4, 4))
    assert sim.is_blocked((4, 4)) is False


def test_obstacle_outside_map_raises_error():
    sim = Simulation()
    with pytest.raises(ValueError):
        sim.add_obstacle((50, 50))


def test_obstacle_on_department_raises_error():
    sim = Simulation()
    with pytest.raises(ValueError):
        sim.add_obstacle(sim.get_location_cell("Pharmacy"))


def test_unknown_location_raises_error():
    sim = Simulation()
    with pytest.raises(ValueError):
        sim.get_location_cell("Cafeteria")


def test_straight_path_without_obstacles():
    sim = Simulation()
    assert sim.find_path((1, 1), (3, 1)) == [(1, 1), (2, 1), (3, 1)]


def test_path_goes_around_obstacle():
    sim = Simulation()
    sim.add_obstacle((2, 1))
    path = sim.find_path((1, 1), (3, 1))
    assert path[0] == (1, 1)
    assert path[-1] == (3, 1)
    assert (2, 1) not in path
    assert len(path) == 5


def test_no_path_when_goal_is_walled_in():
    sim = Simulation(width=5, height=5)
    for cell in [(3, 4), (4, 3)]:
        sim.add_obstacle(cell)
    assert sim.find_path((0, 0), (4, 4)) == []


def test_path_to_same_cell():
    sim = Simulation()
    assert sim.find_path((2, 2), (2, 2)) == [(2, 2)]