from mesa import Agent
from enum import Enum
import numpy as np
from collections import deque
import heapq


class RoombaActions(Enum):
    MOVE_UP = "up"
    MOVE_DOWN = "down"
    MOVE_LEFT = "left"
    MOVE_RIGHT = "right"
    CLEAN = "clean"
    CHARGE = "charge"
    IDLE = "idle"


class CellKnowledge(Enum):
    UNKNOWN = 0
    WALL = 1
    OBSTACLE = 2
    CHARGING_STATION = 3
    EMPTY = 4
    DIRTY = 5


class Roomba(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.battery = 100
        self.pos = pos
        self.home_charger = None
        self.last_action = RoombaActions.IDLE
        self.movements = 0

        self.BATTERY_CRITICAL = 20 
        self.BATTERY_SAFE = 90 
        self.MOVE_COST = 1  
        self.CLEAN_COST = 2  
        self.CHARGE_RATE = 10  

        # Knowledge and memory systems
        self.knowledge_matrix = np.full((3, 3), CellKnowledge.UNKNOWN.value)
        self.matrix_center = (1, 1)  
        self.dirty_cells_memory = set()
        self.visited_cells = set()
        self.explored_cells = set()

    def estimate_return_cost(self):
        """Estimate battery needed to return to charging station"""
        if not self.home_charger:
            return 0

        path = self.find_path_to_target(self.home_charger)
        if path:
            return len(path) * self.MOVE_COST
        # Fallback to Manhattan distance if no path found
        return abs(self.pos[0] - self.home_charger[0]) + abs(
            self.pos[1] - self.home_charger[1]
        )

    def should_return_to_charger(self):
        """Determine if Roomba should return to charger"""

        # First check if battery is critical
        if self.battery <= self.BATTERY_CRITICAL:
            return True

        # Calculate Manhattan distance to charger
        manhattan_distance = abs(self.pos[0] - self.home_charger[0]) + abs(
            self.pos[1] - self.home_charger[1]
        )

        # Get actual path cost if possible
        path = self.find_path_to_target(self.home_charger)
        path_cost = (
            len(path) * self.MOVE_COST if path else manhattan_distance * self.MOVE_COST
        )

        # Add safety margin
        return_cost = path_cost + 15  

        should_return = self.battery <= return_cost + self.BATTERY_CRITICAL
        return should_return

    def charge_battery(self):
        """Modified charging with higher rate"""
        current_cell = self.get_cell_at_pos(self.pos)
        if current_cell and current_cell.state == "charging_station":
            self.battery = min(100, self.battery + self.CHARGE_RATE)
            self.last_action = RoombaActions.CHARGE
            return True
        return False

    def expand_knowledge_matrix(self, direction):
        """Expands the knowledge matrix when discovering new areas"""
        current_shape = self.knowledge_matrix.shape

        if direction == "north":
            new_row = np.full((1, current_shape[1]), CellKnowledge.UNKNOWN.value)
            self.knowledge_matrix = np.vstack((new_row, self.knowledge_matrix))
            self.matrix_center = (self.matrix_center[0] + 1, self.matrix_center[1])

        elif direction == "south":
            new_row = np.full((1, current_shape[1]), CellKnowledge.UNKNOWN.value)
            self.knowledge_matrix = np.vstack((self.knowledge_matrix, new_row))

        elif direction == "west":
            new_col = np.full((current_shape[0], 1), CellKnowledge.UNKNOWN.value)
            self.knowledge_matrix = np.hstack((new_col, self.knowledge_matrix))
            self.matrix_center = (self.matrix_center[0], self.matrix_center[1] + 1)

        elif direction == "east":
            new_col = np.full((current_shape[0], 1), CellKnowledge.UNKNOWN.value)
            self.knowledge_matrix = np.hstack((self.knowledge_matrix, new_col))

    def update_knowledge(self):
        """Update knowledge of the environment"""
        self.visited_cells.add(self.pos)
        matrix_x = self.matrix_center[0]
        matrix_y = self.matrix_center[1]

        if matrix_x <= 1:
            self.expand_knowledge_matrix("north")
        if matrix_x >= self.knowledge_matrix.shape[0] - 2:
            self.expand_knowledge_matrix("south")
        if matrix_y <= 1:
            self.expand_knowledge_matrix("west")
        if matrix_y >= self.knowledge_matrix.shape[1] - 2:
            self.expand_knowledge_matrix("east")

        # Update current cell knowledge
        current_cell = self.get_cell_at_pos(self.pos)
        if current_cell:
            if current_cell.state == "obstacle":
                self.knowledge_matrix[matrix_x, matrix_y] = CellKnowledge.OBSTACLE.value
            elif current_cell.state == "charging_station":
                self.knowledge_matrix[matrix_x, matrix_y] = (
                    CellKnowledge.CHARGING_STATION.value
                )
            elif current_cell.state == "dirty":
                self.knowledge_matrix[matrix_x, matrix_y] = CellKnowledge.DIRTY.value
                self.dirty_cells_memory.add(self.pos)
            else:
                self.knowledge_matrix[matrix_x, matrix_y] = CellKnowledge.EMPTY.value
                if self.pos in self.dirty_cells_memory:
                    self.dirty_cells_memory.remove(self.pos)

        # Update adjacent cells knowledge
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            adj_x = matrix_x + dx
            adj_y = matrix_y + dy
            world_pos = (self.pos[0] + dx, self.pos[1] + dy)

            adj_cell = self.get_cell_at_pos(world_pos)
            if adj_cell:
                self.explored_cells.add(world_pos)
                if adj_cell.state == "obstacle":
                    self.knowledge_matrix[adj_x, adj_y] = CellKnowledge.OBSTACLE.value
                elif adj_cell.state == "charging_station":
                    self.knowledge_matrix[adj_x, adj_y] = (
                        CellKnowledge.CHARGING_STATION.value
                    )
                elif adj_cell.state == "dirty":
                    self.knowledge_matrix[adj_x, adj_y] = CellKnowledge.DIRTY.value
                    self.dirty_cells_memory.add(world_pos)
                else:
                    self.knowledge_matrix[adj_x, adj_y] = CellKnowledge.EMPTY.value
            else:
                self.knowledge_matrix[adj_x, adj_y] = CellKnowledge.WALL.value

    def get_cell_at_pos(self, pos):
        """Get cell at specific position"""
        if not (
            0 <= pos[0] < self.model.grid.width and 0 <= pos[1] < self.model.grid.height
        ):
            return None

        cell_contents = self.model.grid.get_cell_list_contents([pos])
        for content in cell_contents:
            if hasattr(content, "state"):
                return content
        return None

    def find_path_to_target(self, target_pos):
        """A* pathfinding implementation"""
        def is_valid_move(pos):
            if not self.is_valid_position(pos):
                return False
            cell = self.get_cell_at_pos(pos)
            return not (cell and hasattr(cell, "state") and cell.state == "obstacle")

        def heuristic(pos1, pos2):
            return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

        start = self.pos
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, target_pos)}

        while open_set:
            current = min(open_set, key=lambda x: x[0])[1]
            if current == target_pos:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path

            open_set = [(f, pos) for f, pos in open_set if pos != current]

            for next_pos in self.get_possible_moves():
                if not is_valid_move(next_pos):
                    continue
                tentative_g_score = g_score[current] + 1
                if next_pos not in g_score or tentative_g_score < g_score[next_pos]:
                    came_from[next_pos] = current
                    g_score[next_pos] = tentative_g_score
                    f_score[next_pos] = g_score[next_pos] + heuristic(
                        next_pos, target_pos
                    )
                    open_set.append((f_score[next_pos], next_pos))
        return None

    def get_unexplored_frontier(self):
        """Get positions adjacent to known cells that are still unknown"""
        frontier = set()
        for explored in self.explored_cells:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                adj_pos = (explored[0] + dx, explored[1] + dy)
                if adj_pos not in self.explored_cells:
                    if self.is_valid_position(adj_pos):
                        frontier.add(adj_pos)
        return frontier

    def is_valid_position(self, pos):
        """Check if a position is valid"""
        return (
            0 <= pos[0] < self.model.grid.width and 0 <= pos[1] < self.model.grid.height
        )

    def move(self, new_pos):
        """Execute movement with battery management"""
        if self.battery < self.MOVE_COST:
            return False

        if not self.is_valid_position(new_pos):
            return False

        cell_contents = self.model.grid.get_cell_list_contents([new_pos])
        if any(
            hasattr(content, "state") and content.state == "obstacle"
            for content in cell_contents
        ):
            return False

        self.model.grid.remove_agent(self)
        self.model.grid.place_agent(self, new_pos)
        self.pos = new_pos
        self.battery -= self.MOVE_COST  
        self.movements += 1
        self.update_knowledge()
        return True

    def clean_current_cell(self):
        """Clean current cell if dirty"""
        if self.battery <= 0:
            return False

        current_cell = self.get_cell_at_pos(self.pos)
        if current_cell and current_cell.state == "dirty":
            current_cell.set_state("clean")
            self.battery -= 1
            self.last_action = RoombaActions.CLEAN
            if self.pos in self.dirty_cells_memory:
                self.dirty_cells_memory.remove(self.pos)
            return True
        return False

    def get_possible_moves(self):
        """Get all valid moves from current position"""
        possible_moves = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            new_pos = (self.pos[0] + dx, self.pos[1] + dy)
            if self.is_valid_position(new_pos):
                cell_contents = self.model.grid.get_cell_list_contents([new_pos])
                if not any(
                    hasattr(content, "state") and content.state == "obstacle"
                    for content in cell_contents
                ):
                    possible_moves.append(new_pos)
        return possible_moves

    def step(self):
        """Main decision-making logic"""
        self.update_knowledge()

        # Check if at charging station and should charge
        if self.pos == self.home_charger and self.battery < self.BATTERY_SAFE:
            self.charge_battery()
            return

        # Check if should return to charger
        if self.should_return_to_charger():
            path = self.find_path_to_target(self.home_charger)
            if path and len(path) > 1:
                if self.battery >= self.MOVE_COST:
                    next_pos = path[1]
                    # Verify the next position is actually reachable
                    if next_pos in self.get_possible_moves():
                        self.move(next_pos)
                        return
            
            # If no path or next move isn't possible, try emergency 
            possible_moves = self.get_possible_moves()
            if possible_moves:
                # Sort moves by distance to charger
                moves_with_distances = [
                    (abs(pos[0] - self.home_charger[0]) + abs(pos[1] - self.home_charger[1]), pos)
                    for pos in possible_moves
                ]
                moves_with_distances.sort()  # Sort by distance
                
                # Try moves in order of closest to charger
                for _, move_pos in moves_with_distances:
                    # Double check this move 
                    if self.battery >= self.MOVE_COST:
                        if self.move(move_pos):
                            return
    
                self.BATTERY_CRITICAL += 5  
                return

        # Clean current cell if dirty
        if self.clean_current_cell():
            return

        # Go to nearest known dirty cell
        if self.dirty_cells_memory:
            nearest_dirty = min(
                self.dirty_cells_memory,
                key=lambda pos: abs(pos[0] - self.pos[0]) + abs(pos[1] - self.pos[1]),
            )
            path = self.find_path_to_target(nearest_dirty)
            if path and len(path) > 1:
                self.move(path[1])
                return

        # Explore unknown areas
        frontier = self.get_unexplored_frontier()
        if frontier:
            nearest_frontier = min(
                frontier,
                key=lambda pos: abs(pos[0] - self.pos[0]) + abs(pos[1] - self.pos[1]),
            )
            path = self.find_path_to_target(nearest_frontier)
            if path and len(path) > 1:
                self.move(path[1])
                return

        # If nothing else to do, move randomly
        possible_moves = self.get_possible_moves()
        if possible_moves:
            self.move(self.random.choice(possible_moves))
