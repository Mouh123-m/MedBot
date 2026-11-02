from datetime import datetime

VALID_PRIORITIES = ("Low", "Normal", "High", "Urgent")


class Mission:
    def __init__(self, mission_id, start, destination, priority="Normal"):
        if not start or not destination:
            raise ValueError("Start and destination are required")
        if start == destination:
            raise ValueError("Start and destination must be different")
        if priority not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority: {priority}")

        self.mission_id = mission_id
        self.start = start
        self.destination = destination
        self.priority = priority
        self.status = "pending"
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.failure_reason = None

    def start_mission(self):
        if self.status != "pending":
            raise ValueError("Only a pending mission can be started")
        self.status = "in_progress"

    def complete(self):
        if self.status != "in_progress":
            raise ValueError("Only a mission in progress can be completed")
        self.status = "completed"

    def fail(self, reason):
        if self.status not in ("pending", "in_progress"):
            raise ValueError("Mission is already finished")
        self.status = "failed"
        self.failure_reason = reason

    def to_dict(self):
        return {
            "mission_id": self.mission_id,
            "start": self.start,
            "destination": self.destination,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "failure_reason": self.failure_reason,
        }