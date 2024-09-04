
import heapq
import agentpy as ap
from matplotlib import pyplot as plt
import IPython
from owlready2 import *
import numpy as np


onto = get_ontology("file://onto_warehouse.owl")


with onto:
    class Entity(Thing):
        pass

    class Drone(Entity):
        pass

    class Guard(Entity):
        pass

    class Object(Entity):
        pass

    class Camera(Object):
        pass

    class Coordinate(Thing):
        pass

    class Position(Coordinate):
        pass

    class has_place(ObjectProperty, FunctionalProperty):
        domain = [Entity]
        range = [Coordinate]

    class has_position(DataProperty, FunctionalProperty):
        domain = [Coordinate]
        range = [str]

    class controls(ObjectProperty):
        domain = [Guard]
        range = [Camera]


class WarehouseGuard(ap.Agent):
    pass


class WarehouseDrone(ap.Agent):
    pass


class WarehouseCamera(ap.Agent):
    pass


class WarehouseObstacle(ap.Agent):
    pass


def astar(grid, start, goal):
    open_set = []
    pos = grid.positions[start]
    heapq.heappush(open_set, (0, pos))

    came_from = {}
    g_score = {pos: 0}
    f_score = {pos: heuristic(pos, goal)}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            return reconstruct_path(came_from, current)

        for direction in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            neighbor_pos = (current[0] + direction[0],
                            current[1] + direction[1])

            if 0 <= neighbor_pos[0] < grid.shape[0] and 0 <= neighbor_pos[1] < grid.shape[1]:
                location = grid.grid[neighbor_pos[0]][neighbor_pos[1]]
                if type(location) == np.record:
                    agent_set = location[0]
                    blocked = False
                    for agent in agent_set:
                        if isinstance(agent, WarehouseObstacle):
                            blocked = True
                            break
                    if blocked:
                        continue
                tentative_g_score = g_score[current] + 1

                if neighbor_pos not in g_score or tentative_g_score < g_score[neighbor_pos]:
                    came_from[neighbor_pos] = current
                    g_score[neighbor_pos] = tentative_g_score
                    f_score[neighbor_pos] = tentative_g_score + \
                        heuristic(neighbor_pos, goal)
                    heapq.heappush(
                        open_set, (f_score[neighbor_pos], neighbor_pos))

    return []


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruct_path(came_from, current):
    total_path = [current]
    while current in came_from:
        current = came_from[current]
        total_path.append(current)
    return total_path[::-1]


class WarehouseCamera(ap.Agent):
    def setup(self):
        self.agentType = 1
        self.active = False


class WarehouseDrone(ap.Agent):
    def setup(self):
        self.agentType = 0
        self.position = (0, 0)
        self.patrol_route = []
        self.current_patrol_target = -1
        self.path = []
        self.rules = [
            self.rule_move,
        ]
        self.actions = [
            self.move_towards_target,
        ]
        self.target = None
        self.moves = 0
        self.alert = False

    def next(self):
        for act in self.actions:
            for rule in self.rules:
                if rule(act):
                    act()

    def step(self, position, target, alert=False):
        self.position = position
        self.model.grid.move_to(self, position)
        self.alert = alert
        if self.alert:
            self.target = target
        self.next()

    def rule_move(self, act):
        return act == self.move_towards_target

    def move(self):
        self.model.grid.move_to(self, self.target)
        self.moves += 1

    def find_shortest_path(self, target):
        path = astar(self.model.grid, self, target)
        if path and len(path) > 1:
            self.path = path

    def patrol(self):
        if self.current_patrol_target == -1:
            nearest = float('inf')
            for i, coord in enumerate(self.patrol_route):
                dist = heuristic(self.position, coord)
                if dist < nearest:
                    nearest = dist
                    self.current_patrol_target = i
        target = self.patrol_route[self.current_patrol_target]
        self.find_shortest_path(target)
        self.current_patrol_target += 1

    def move_towards_target(self):
        if self.alert:
            self.current_patrol_target = -1
            self.find_shortest_path()
        else:
            self.patrol()
        if self.target != self.position:
            self.move()


class WarehouseGuard(ap.Agent):
    def setup(self):
        self.agentType = 2
        self.alert = False
        self.controlling_camera = None


class WarehouseObstacle(ap.Agent):
    def setup(self):
        self.agentType = 3


class WarehouseModel(ap.Model):
    def setup(self):
        self.grid = ap.Grid(self, (self.p.M, self.p.N), track_empty=True)
        self.drones = ap.AgentList(self, self.p.drones, WarehouseDrone)
        self.cameras = ap.AgentList(self, self.p.cameras, WarehouseCamera)
        self.guard = ap.AgentList(self, self.p.guards, WarehouseGuard)
        self.obstacles = ap.AgentList(
            self, self.p.obstacles, WarehouseObstacle)

        self.grid.add_agents(self.drones, position=self.p.drone_positions)
        self.grid.add_agents(self.obstacles, positions=[(5, 5)])
        for drone, patrol in zip(self.drones, self.p.patrol_route):
            drone.patrol_route = patrol

        self.steps = 0

    def step(self, position, target, alert=False):
        self.drones.step(position, target, alert)
        self.steps += 1
        return [drone.path for drone in self.drones]

    def end(self):
        return {
            'steps': self.steps,
            'positions': [self.grid.positions[drone] for drone in self.drones],
        }
