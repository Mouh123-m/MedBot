import json

from src.medical_robot import MedicalRobot
from src.mission_manager import MissionManager
from src.simulation import Simulation


def run_until_finished(manager):
    steps = 0
    while manager.current_mission is not None:
        manager.step()
        steps += 1
        assert steps < 500
    return steps


def test_full_scenario_with_two_missions_and_obstacle(tmp_path):
    history_file = tmp_path / "history.json"
    sim = Simulation()
    robot = MedicalRobot(sim)
    manager = MissionManager(robot, str(history_file))

    first = manager.create_mission("Pharmacy", "Laboratory", "High")
    manager.start_mission(first.mission_id)
    run_until_finished(manager)
    assert first.status == "completed"
    assert robot.position == sim.get_location_cell("Laboratory")

    second = manager.create_mission("Laboratory", "Emergency Department", "Urgent")
    manager.start_mission(second.mission_id)
    manager.step()
    for cell in list(robot.path)[:3]:
        if cell != sim.get_location_cell("Emergency Department"):
            sim.add_obstacle(cell)
            break
    run_until_finished(manager)
    assert second.status == "completed"
    assert robot.position == sim.get_location_cell("Emergency Department")

    stats = manager.get_statistics()
    assert stats == {"total": 2, "completed": 2, "failed": 0, "pending": 0}

    saved = json.loads(history_file.read_text(encoding="utf-8"))
    assert [record["status"] for record in saved] == ["completed", "completed"]


def test_stopped_mission_is_saved_as_failed(tmp_path):
    history_file = tmp_path / "history.json"
    robot = MedicalRobot(Simulation())
    manager = MissionManager(robot, str(history_file))

    mission = manager.create_mission("Pharmacy", "Patient Rooms")
    manager.start_mission(mission.mission_id)
    manager.step()
    manager.stop_current()

    saved = json.loads(history_file.read_text(encoding="utf-8"))
    assert saved[0]["status"] == "failed"
    assert saved[0]["failure_reason"] == "Mission stopped by user"
    assert robot.is_available() is True