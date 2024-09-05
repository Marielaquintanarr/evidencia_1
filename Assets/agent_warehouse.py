
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


def visualize_grid(model):
    """
    Function to visualize the grid with drones, cameras, guards, and obstacles at the start.
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    # Create a blank grid
    grid_shape = model.grid.shape
    grid = np.zeros(grid_shape)

    # Plot drones
    for drone in model.drones:
        pos = model.grid.positions[drone]
        ax.scatter(pos[0], pos[1], color='blue',
                   s=100, label='Drone', marker='o')

    for drone in model.drones:
        patrol_route = drone.patrol_route
        # Check if the drone has a patrol route
        if patrol_route and len(patrol_route) > 1:
            # Plot lines connecting the patrol route points
            patrol_x = [p[0] for p in patrol_route]
            patrol_y = [p[1] for p in patrol_route]
            ax.plot(patrol_x, patrol_y, color='blue',
                    linestyle='--', marker='o', label='Patrol Route')
            # Optionally, add arrows to indicate direction
            for i in range(len(patrol_route) - 1):
                ax.arrow(patrol_route[i][0], patrol_route[i][1],
                         patrol_route[i+1][0] - patrol_route[i][0],
                         patrol_route[i+1][1] - patrol_route[i][1],
                         head_width=0.3, head_length=0.3, fc='blue', ec='blue')

    # Plot obstacles
    for obstacle in model.obstacles:
        pos = model.grid.positions[obstacle]
        ax.scatter(pos[0], pos[1], color='black',
                   s=100, label='Obstacle', marker='s')

    # Set grid display parameters
    ax.set_xlim(0, grid_shape[0])
    ax.set_ylim(0, grid_shape[1])
    ax.set_xticks(np.arange(grid_shape[0]))
    ax.set_yticks(np.arange(grid_shape[1]))
    ax.grid(True)

    # Avoid duplicate labels
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())

    # Display the plot
    plt.gca().set_aspect('equal', adjustable='box')
    plt.title('Initial Grid Setup')
    plt.show()


def astar(grid, agent, start, goal):
    """
    A* algorithm for finding the shortest path in an AgentPy grid.

    Parameters:
    - grid (Grid): The AgentPy grid where the agents are located.
    - start (tuple): The starting position (x, y).
    - goal (tuple): The goal position (x, y).

    Returns:
    - path (list): A list of grid positions representing the shortest path.
    """

    open_list = []
    heapq.heappush(open_list, (0, start))

    g_cost = {start: 0}

    came_from = {start: None}

    while open_list:
        _, current_pos = heapq.heappop(open_list)
        grid.move_to(agent, current_pos)

        if current_pos == goal:
            path = []
            while current_pos:
                path.append(current_pos)
                current_pos = came_from[current_pos]
            return path[::-1]  # Return reversed path

        neighbors = {(current_pos[0] + dx, current_pos[1] + dy) for dx in range(-1, 2)
                     for dy in range(-1, 2) if not (dx == 0 and dy == 0)}
        occupied = {grid.positions[neighbor]
                    for neighbor in grid.neighbors(agent)}
        for neighbor in neighbors - occupied:
            new_cost = g_cost[current_pos] + 1

            if neighbor not in g_cost or new_cost < g_cost[neighbor]:
                g_cost[neighbor] = new_cost
                priority = new_cost + manhattan_distance(neighbor, goal)
                heapq.heappush(open_list, (priority, neighbor))
                came_from[neighbor] = current_pos

    return None


def manhattan_distance(a, b):
    """Heuristic function: Manhattan distance between two points."""
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

    def step(self, position, target=None, alert=False):
        self.position = position
        self.alert = alert
        if self.alert:
            self.target = target
        self.next()

    def rule_move(self, act):
        return act == self.move_towards_target

    def move(self):
        self.model.grid.move_to(self, self.position)
        self.moves += 1

    def find_shortest_path(self, target):
        print('target', target)
        path = astar(self.model.grid, self, tuple(
            self.position), tuple(target))
        self.model.grid.move_to(self, self.position)
        print('path', path)
        if path and len(path) > 1:
            self.path = path

    def patrol(self):
        self.move()
        if self.current_patrol_target == -1:
            nearest = float('inf')
            for i, coord in enumerate(self.patrol_route):
                dist = manhattan_distance(self.position, coord)
                if dist < nearest:
                    nearest = dist
                    self.current_patrol_target = i
        target = self.patrol_route[self.current_patrol_target]
        self.find_shortest_path(target)
        self.current_patrol_target += 1
        if self.current_patrol_target >= len(self.patrol_route):
            self.current_patrol_target = 0

    def move_towards_target(self):
        if self.alert:
            self.move()
            self.current_patrol_target = -1
            self.find_shortest_path(self.target)
        else:
            self.patrol()

    def assign_patrol_route(self, route):
        self.patrol_route = route


class WarehouseGuard(ap.Agent):
    def setup(self):
        self.agentType = 2
        self.alert = False
        self.controlling_camera = None


class WarehouseObstacle(ap.Agent):
    def setup(self):
        self.agentType = 3


def get_rectangle_positions(top_left, bottom_right):
    """Generate all the positions inside a rectangle."""
    positions = []
    if top_left[0] > bottom_right[0] or top_left[1] > bottom_right[1]:
        raise ValueError('Invalid rectangle coordinates')
    for x in range(top_left[0], bottom_right[0] + 1):
        for y in range(top_left[1], bottom_right[1] + 1):
            positions.append((x, y))
    print(positions)
    return positions


class WarehouseModel(ap.Model):
    def setup(self):
        self.grid = ap.Grid(self, (self.p.M, self.p.N), track_empty=True)
        self.drones = ap.AgentList(self, self.p.drones, WarehouseDrone)
        self.cameras = ap.AgentList(self, self.p.cameras, WarehouseCamera)
        self.guard = ap.AgentList(self, self.p.guards, WarehouseGuard)

        self.grid.add_agents(self.drones, random=True, empty=True)
        for drone, position in zip(self.drones, self.p.drone_positions):
            self.grid.move_to(drone, position)
        for drone, patrol in zip(self.drones, self.p.patrol_routes):
            drone.patrol_route = patrol

        obstacles = []
        for area in self.p.obstacles:
            obstacles += get_rectangle_positions(area[0], area[1])
        self.obstacles = ap.AgentList(self, len(obstacles), WarehouseObstacle)
        self.grid.add_agents(self.obstacles, positions=obstacles)

        self.steps = 0

    def step(self, positions, target=None, alert=False):
        for drone, position in zip(self.drones, positions):
            drone.step(position, target, alert)
        self.steps += 1
        return [drone.path for drone in self.drones]

    def end(self):
        return {
            'steps': self.steps,
            'positions': [self.grid.positions[drone] for drone in self.drones],
        }
