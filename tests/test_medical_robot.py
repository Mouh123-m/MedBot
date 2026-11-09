import pytest

from src.medical_robot import MedicalRobot
from src.simulation import Simulation


def make_robot(width=10, height=10, start=(1, 1)):
    sim = Simulation(width=width, height=height)
    robot = MedicalRobot(sim, start_cell=start)
    return sim, robot


def test_new_robot_is_idle_and_available():
    sim, robot = make_robot()
    assert robot.status == "idle"
    assert robot.is_available() is True
    assert robot.position == (1, 1)


def test_start_trip_sets_moving_status():
    sim, robot = make_robot()
    assert robot.start_trip((3, 1)) is True
    assert robot.status == "moving"
    assert robot.is_available() is False


def test_start_trip_returns_false_when_no_path():
    sim, robot = make_robot(width=5, height=5, start=(0, 0))
    sim.add_obstacle((3, 4))
    sim.add_obstacle((4, 3))
    assert robot.start_trip((4, 4)) is False
    assert robot.status == "idle"


def test_robot_reaches_destination():
    sim, robot = make_robot()
    robot.start_trip((3, 1))
    results = []
    while robot.status == "moving":
        results.append(robot.move_step())
    assert results[-1] == "arrived"
    assert robot.position == (3, 1)
    assert robot.status == "idle"


def test_busy_robot_rejects_new_trip():
    sim, robot = make_robot()
    robot.start_trip((3, 1))
    with pytest.raises(ValueError):
        robot.start_trip((5, 5))


def test_obstacle_triggers_reroute():
    sim, robot = make_robot()
    robot.start_trip((4, 1))
    robot.move_step()
    sim.add_obstacle((3, 1))
    result = robot.move_step()
    assert result == "rerouted"
    assert robot.alert == "Obstacle detected at (3, 1)"
    assert robot.status == "moving"
    while robot.status == "moving":
        robot.move_step()
    assert robot.position == (4, 1)


def test_obstacle_without_alternative_blocks_robot():
    sim, robot = make_robot(width=5, height=1, start=(0, 0))
    robot.start_trip((4, 0))
    robot.move_step()
    sim.add_obstacle((2, 0))
    result = robot.move_step()
    assert result == "blocked"
    assert robot.status == "blocked"
    assert robot.path == []


def test_pause_and_resume():
    sim, robot = make_robot()
    robot.start_trip((3, 1))
    robot.pause()
    assert robot.status == "paused"
    position_before = robot.position
    robot.move_step()
    assert robot.position == position_before
    robot.resume()
    assert robot.status == "moving"


def test_stop_clears_trip():
    sim, robot = make_robot()
    robot.start_trip((5, 5))
    robot.stop()
    assert robot.status == "stopped"
    assert robot.path == []
    assert robot.destination is None