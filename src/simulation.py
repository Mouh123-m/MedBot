from collections import deque


class Simulation:
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.locations = {
            "Pharmacy": (1, 1),
            "Emergency Department": (8, 1),
            "Laboratory": (1, 8),
            "Patient Rooms": (8, 8),
        }
        self.obstacles = set()

    def is_inside(self, cell):
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def is_blocked(self, cell):
        return (not self.is_inside(cell)) or (cell in self.obstacles)

    def add_obstacle(self, cell):
        if not self.is_inside(cell):
            raise ValueError("Cell is outside the map")
        if cell in self.locations.values():
            raise ValueError("Cannot place an obstacle on a department")
        self.obstacles.add(cell)

    def remove_obstacle(self, cell):
        self.obstacles.discard(cell)

    def get_location_cell(self, name):
        if name not in self.locations:
            raise ValueError(f"Unknown location: {name}")
        return self.locations[name]

    def find_path(self, start, goal):
        if self.is_blocked(start) or self.is_blocked(goal):
            return []
        if start == goal:
            return [start]

        queue = deque([start])
        came_from = {start: None}

        while queue:
            current = queue.popleft()
            if current == goal:
                break
            x, y = current
            for neighbor in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                if neighbor not in came_from and not self.is_blocked(neighbor):
                    came_from[neighbor] = current
                    queue.append(neighbor)

        if goal not in came_from:
            return []

        path = []
        cell = goal
        while cell is not None:
            path.append(cell)
            cell = came_from[cell]
        path.reverse()
        return path
    