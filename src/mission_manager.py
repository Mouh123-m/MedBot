import json
import os

from src.mission import Mission


class MissionManager:
    def __init__(self, robot, history_file="missions_history.json"):
        self.robot = robot
        self.history_file = history_file
        self.missions = []
        self.current_mission = None
        self._next_id = 1
        self.load_history()

    def create_mission(self, start, destination, priority="Normal"):
        mission = Mission(self._next_id, start, destination, priority)
        self._next_id += 1
        self.missions.append(mission)
        self.save_history()
        return mission

    def start_mission(self, mission_id):
        if self.current_mission is not None:
            raise ValueError("Another mission is already running")
        mission = self.get_mission(mission_id)
        if not self.robot.is_available():
            raise ValueError("Robot is not available")

        simulation = self.robot.simulation
        start_cell = simulation.get_location_cell(mission.start)
        goal_cell = simulation.get_location_cell(mission.destination)

        if self.robot.position != start_cell:
            if not self.robot.start_trip(start_cell):
                mission.start_mission()
                self._finish(mission, False, "No path to the start location")
                return mission
            while self.robot.status == "moving":
                self.robot.move_step()
            if self.robot.position != start_cell:
                mission.start_mission()
                self._finish(mission, False, "Could not reach the start location")
                return mission

        mission.start_mission()
        if not self.robot.start_trip(goal_cell):
            self._finish(mission, False, "No path to the destination")
            return mission

        self.current_mission = mission
        self.save_history()
        return mission

    def step(self):
        if self.current_mission is None:
            return None
        result = self.robot.move_step()
        if result == "arrived":
            self._finish(self.current_mission, True, None)
        elif result == "blocked":
            self._finish(self.current_mission, False, "Obstacle with no alternative path")
        elif self.robot.status == "stopped":
            self._finish(self.current_mission, False, "Mission stopped by user")
        return result

    def stop_current(self):
        if self.current_mission is None:
            return
        self.robot.stop()
        self._finish(self.current_mission, False, "Mission stopped by user")

    def _finish(self, mission, success, reason):
        if success:
            mission.complete()
        else:
            mission.fail(reason)
        self.current_mission = None
        if self.robot.status in ("stopped", "blocked"):
            self.robot.status = "idle"
        self.save_history()

    def get_mission(self, mission_id):
        for mission in self.missions:
            if mission.mission_id == mission_id:
                return mission
        raise ValueError(f"Mission not found: {mission_id}")

    def get_history(self):
        return [m.to_dict() for m in self.missions]

    def get_statistics(self):
        total = len(self.missions)
        completed = sum(1 for m in self.missions if m.status == "completed")
        failed = sum(1 for m in self.missions if m.status == "failed")
        pending = sum(1 for m in self.missions if m.status == "pending")
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
        }

    def save_history(self):
        with open(self.history_file, "w", encoding="utf-8") as file:
            json.dump(self.get_history(), file, indent=2)

    def load_history(self):
        if not os.path.exists(self.history_file):
            return
        with open(self.history_file, "r", encoding="utf-8") as file:
            records = json.load(file)
        for record in records:
            mission = Mission(
                record["mission_id"],
                record["start"],
                record["destination"],
                record["priority"],
            )
            mission.status = record["status"]
            mission.created_at = record["created_at"]
            mission.failure_reason = record["failure_reason"]
            self.missions.append(mission)
        if self.missions:
            self._next_id = max(m.mission_id for m in self.missions) + 1