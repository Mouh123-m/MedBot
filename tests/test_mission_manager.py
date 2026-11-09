import json

import pytest

from src.medical_robot import MedicalRobot
from src.mission_manager import MissionManager
from src.simulation import Simulation


def make_manager(tmp_path):
    sim = Simulation()
    robot = MedicalRobot(sim)
    history_file = tmp_path / "history.json"
    manager = MissionManager(robot, str(history_file))
    return sim, robot, manager


def run_until_finished(manager):
    steps = 0
    while manager.current_mission is not None:
        manager.step()
        steps += 1
        assert steps < 500
    return steps


def test_create_mission_adds_pending_mission(tmp_path):
    sim, robot, manager = make_manager(tmp_path)
    mission = manager.create_mission("Pharmacy", "Laboratory", "High")
    assert mission.status == "pending"
    assert manager.get_statistics()["pending"] == 1


def test_invalid_mission_is_rejected(tmp_path):
    sim, robot, manager = make_manager(tmp_path)
    with pytest.raises(ValueError):
        manager.create_mission("Pharmacy", "Pharmacy")
    assert manager.get_statistics()["total"] == 0


def test_mission_ids_increase(tmp_path):
    sim, robot, manager = make_manager(tmp_path)
    first = manager.create_mission("Pharmacy", "Laboratory")
    second = manager.create_mission("Laboratory", "Patient Rooms")
    assert second.mission_id == first.mission_id + 1


def test_mission_completes_successfully(tmp_path):
    sim, robot, manager = make_manager(tmp_path)
    mission = manager.create_mission("Pharmacy", "Laboratory")
    manager.start_mission(mission.mission_id)
    run_until_finished(manager)
    assert mission.status == "completed"
    assert robot.position == sim.get_location_cell("Laboratory")
    assert robot.is_available() is True


def test_robot_moves_to_start_location_first(tmp_path):
    sim, robot, manager = make_manager(tmp_path)
    mission = manager.create_mission("Laboratory", "Patient Rooms")
    manager.start_mission(mission.mission_id)
    assert robot.position == sim.get_location_cell("Laboratory")
    run_until_finished(manager)
    assert mission.status == "completed"


def test_cannot_start_second_mission_while_running(tmp_path):
    sim, robot, manager = make_manager(tmp_path)
    first = manager.create_mission("Pharmacy", "Laboratory")
    second = manager.create_mission("Pharmacy", "Patient Rooms")
    manager.start_mission(first.mission_id)
    with pytest.raises(ValueError):
        manager.start_mission(second.mission_id)


def test_unknown_mission_id_raises_error(tmp_path):
    sim, robot, manager = make_manager(tmp_path)
    with pytest.raises(ValueError):
        manager.start_mission(999)


def test_stop_current_fails_mission(tmp_path):
    sim, robot, manager = make_manager(tmp_path)
    mission = manager.create_mission("Pharmacy", "Laboratory")
    manager.start_mission(mission.mission_id)
    manager.step()
    manager.stop_current()
    assert mission.status == "failed"
    assert mission.failure_reason == "Mission stopped by user"
    assert robot.is_available() is True


def test_blocked_robot_fails_mission(tmp_path):
    sim = Simulation(width=5, height=1)
    sim.locations = {"A": (0, 0), "B": (4, 0)}
    robot = MedicalRobot(sim, start_cell=(0, 0))
    manager = MissionManager(robot, str(tmp_path / "history.json"))
    mission = manager.create_mission("A", "B")
    manager.start_mission(mission.mission_id)
    manager.step()
    sim.add_obstacle((2, 0))
    run_until_finished(manager)
    assert mission.status == "failed"
    assert mission.failure_reason == "Obstacle with no alternative path"
    assert robot.is_available() is True


def test_reroute_still_completes_mission(tmp_path):
    sim, robot, manager = make_manager(tmp_path)
    mission = manager.create_mission("Pharmacy", "Emergency Department")
    manager.start_mission(mission.mission_id)
    manager.step()
    sim.add_obstacle((4, 1))
    run_until_finished(manager)
    assert mission.status == "completed"


def test_statistics_count_each_status(tmp_path):
    sim, robot, manager = make_manager(tmp_path)
    done = manager.create_mission("Pharmacy", "Laboratory")
    manager.start_mission(done.mission_id)
    run_until_finished(manager)
    manager.create_mission("Pharmacy", "Patient Rooms")
    stats = manager.get_statistics()
    assert stats == {"total": 2, "completed": 1, "failed": 0, "pending": 1}


def test_history_is_saved_and_reloaded(tmp_path):
    sim, robot, manager = make_manager(tmp_path)
    mission = manager.create_mission("Pharmacy", "Laboratory", "Urgent")
    manager.start_mission(mission.mission_id)
    run_until_finished(manager)

    history_file = tmp_path / "history.json"
    saved = json.loads(history_file.read_text(encoding="utf-8"))
    assert saved[0]["status"] == "completed"

    new_robot = MedicalRobot(Simulation())
    reloaded = MissionManager(new_robot, str(history_file))
    assert reloaded.get_statistics()["completed"] == 1
    new_mission = reloaded.create_mission("Pharmacy", "Laboratory")
    assert new_mission.mission_id == mission.mission_id + 1