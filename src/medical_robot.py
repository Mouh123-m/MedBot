class MedicalRobot:
    def __init__(self, simulation, name="MedBot-01", start_cell=(1, 1)):
        self.simulation = simulation
        self.name = name
        self.position = start_cell
        self.status = "idle"
        self.path = []
        self.destination = None
        self.alert = None

    def is_available(self):
        return self.status == "idle"

    def start_trip(self, destination_cell):
        if self.status != "idle":
            raise ValueError("Robot is busy")
        path = self.simulation.find_path(self.position, destination_cell)
        if not path:
            return False
        self.destination = destination_cell
        self.path = path[1:]
        self.status = "moving"
        self.alert = None
        return True

    def move_step(self):
        if self.status != "moving":
            return self.status

        if not self.path:
            self.status = "idle"
            self.destination = None
            return "arrived"

        next_cell = self.path[0]
        if self.simulation.is_blocked(next_cell):
            self.status = "blocked"
            self.alert = f"Obstacle detected at {next_cell}"
            return self._try_alternative_path()

        self.position = self.path.pop(0)
        if not self.path:
            self.status = "idle"
            self.destination = None
            return "arrived"
        return "moving"

    def _try_alternative_path(self):
        new_path = self.simulation.find_path(self.position, self.destination)
        if not new_path:
            self.path = []
            self.destination = None
            return "blocked"
        self.path = new_path[1:]
        self.status = "moving"
        return "rerouted"

    def pause(self):
        if self.status == "moving":
            self.status = "paused"

    def resume(self):
        if self.status == "paused":
            self.status = "moving"

    def stop(self):
        self.status = "stopped"
        self.path = []
        self.destination = None