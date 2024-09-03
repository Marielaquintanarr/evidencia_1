
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


def euclidean(a, b):
    return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)


def reconstruct_path(came_from, current):
    total_path = [current]
    while current in came_from:
        current = came_from[current]
        total_path.append(current)
    return total_path[::-1]


class WarehouseCamera(ap.Agent):
    def setup(self):
        self.agentType = 2
        self.active = False


class WarehouseDrone(ap.Agent):
    def setup(self):
        self.agentType = 0
        self.x = 0
        self.y = 0
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

    def step(self, data):
        self.next()

    def rule_move(self, act):
        return act == self.move_towards_target

    def move(self, target):
        # TODO Change to direct movement from grid based
        x, y = self.model.grid.positions[self]

        while True:
            nx, ny = target
            dx, dy = self.direction
            if x + dx == nx and y + dy == ny:
                break

        self.model.grid.move_by(self, self.direction)
        self.moves += 1

    def find_nearest_object(self):
        # TODO Adapt pathfinding to use euclidean distance
        closest_object = None
        shortest_path = None

        for obj in self.model.objects:
            try:
                obj_pos = self.model.grid.positions[obj]
            except KeyError:
                continue
            path = astar(self.model.grid, self, obj_pos)
            if not closest_object or (path and len(path) < len(shortest_path)):
                closest_object = obj
                shortest_path = path

        self.target = closest_object
        return shortest_path

    def patrol(self):
        pass

    def move_towards_target(self):
        if self.alert:
            path = self.find_nearest_object()
        else:
            path = self.patrol()
        if path and len(path) > 1:
            next_position = path[1]
            self.move(next_position)


class WarehouseGuard(ap.Agent):
    def setup(self):
        self.agentType = 0
        self.alert = False
        self.controlling_camera = None


class WarehouseModel(ap.Model):
    def setup(self, x, y):
        self.drones = ap.AgentList(self, self.p.drones, WarehouseDrone)
        self.cameras = ap.AgentList(self, self.p.cameras, WarehouseCamera)
        self.guard = ap.AgentList(self, self.p.guards, WarehouseGuard)

        # add in specific locations

        self.steps = 0

    def step(self):
        self.robots.step()
        self.steps += 1
        return self.grid.grid

    def get_positions(self):
        pass

    def end(self):
        return {
            'steps': self.steps,
            'positions': self.get_positions()
        }


# SIMULATION:


# parameters = {
# }


# model = WarehouseModel(parameters)

# Run with animation
# model.run()

# animation = ap.animate(model, fig, ax, animation_plot)
# IPython.display.HTML(animation.to_jshtml())
