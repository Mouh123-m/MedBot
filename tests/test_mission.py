import pytest

from src.mission import Mission


def make_mission():
    return Mission(1, "Pharmacy", "Laboratory", "High")


def test_new_mission_is_pending():
    mission = make_mission()
    assert mission.status == "pending"
    assert mission.failure_reason is None


def test_default_priority_is_normal():
    mission = Mission(1, "Pharmacy", "Laboratory")
    assert mission.priority == "Normal"


def test_same_start_and_destination_raises_error():
    with pytest.raises(ValueError):
        Mission(1, "Pharmacy", "Pharmacy")


def test_empty_start_raises_error():
    with pytest.raises(ValueError):
        Mission(1, "", "Laboratory")


def test_invalid_priority_raises_error():
    with pytest.raises(ValueError):
        Mission(1, "Pharmacy", "Laboratory", "Whenever")


def test_mission_lifecycle_to_completed():
    mission = make_mission()
    mission.start_mission()
    assert mission.status == "in_progress"
    mission.complete()
    assert mission.status == "completed"


def test_cannot_complete_pending_mission():
    mission = make_mission()
    with pytest.raises(ValueError):
        mission.complete()


def test_cannot_start_mission_twice():
    mission = make_mission()
    mission.start_mission()
    with pytest.raises(ValueError):
        mission.start_mission()


def test_fail_records_reason():
    mission = make_mission()
    mission.start_mission()
    mission.fail("Obstacle with no alternative path")
    assert mission.status == "failed"
    assert mission.failure_reason == "Obstacle with no alternative path"


def test_cannot_fail_finished_mission():
    mission = make_mission()
    mission.start_mission()
    mission.complete()
    with pytest.raises(ValueError):
        mission.fail("Too late")


def test_to_dict_contains_all_fields():
    data = make_mission().to_dict()
    assert data["mission_id"] == 1
    assert data["start"] == "Pharmacy"
    assert data["destination"] == "Laboratory"
    assert data["priority"] == "High"
    assert data["status"] == "pending"
    assert "created_at" in data
    assert "failure_reason" in data