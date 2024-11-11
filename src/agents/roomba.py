from mesa import Agent
from enum import Enum


class RoombaActions(Enum):
    MOVE_UP = "up"
    MOVE_DOWN = "down"
    MOVE_LEFT = "left"
    MOVE_RIGHT = "right"
    CLEAN = "clean"
    CHARGE = "charge"
    IDLE = "idle"


class Roomba(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.battery = 100  # Start with 100% battery
        self.pos = None  # Initialize position as None
        self.home_charger = None  # Initialize home charger as None
        self.last_action = RoombaActions.IDLE
        self.movements = 0  # Counter for movements

    def move(self, new_pos):
        """Try to move to a new position"""
        if self.battery <= 0:
            return False

        # Check if the new position is within grid bounds
        if not (
            0 <= new_pos[0] < self.model.grid.width
            and 0 <= new_pos[1] < self.model.grid.height
        ):
            return False

        # Check for obstacles
        cell_contents = self.model.grid.get_cell_list_contents([new_pos])
        for content in cell_contents:
            if hasattr(content, "state") and content.state == "obstacle":
                return False

        # Remove agent from current position before moving
        self.model.grid.remove_agent(self)
        # Move to new position
        self.model.grid.place_agent(self, new_pos)
        self.battery -= 1  # Moving costs 1% battery
        self.movements += 1  # Increment movement counter
        return True

    def get_cell_at_pos(self, pos):
        """Get the cell at a specific position"""
        cell_contents = self.model.grid.get_cell_list_contents([pos])
        for content in cell_contents:
            if hasattr(content, "state"):
                return content
        return None

    def clean_current_cell(self):
        """Clean the current cell if it's dirty"""
        if self.battery <= 0:
            return False

        current_cell = self.get_cell_at_pos(self.pos)
        if current_cell and current_cell.state == "dirty":
            current_cell.set_state("clean")
            self.battery -= 1  # Cleaning costs 1% battery
            self.last_action = RoombaActions.CLEAN
            return True
        return False

    def charge_battery(self):
        """Charge battery if at charging station"""
        current_cell = self.get_cell_at_pos(self.pos)
        if current_cell and current_cell.state == "charging_station":
            self.battery = min(100, self.battery + 5)  # Charge 5% per step
            self.last_action = RoombaActions.CHARGE
            return True
        return False

    def get_possible_moves(self):
        """Get all possible moves from current position"""
        possible_moves = []
        x, y = self.pos

        # Check all adjacent cells
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:  # up, down, right, left
            new_pos = (x + dx, y + dy)

            # Check if position is within grid bounds
            if not (
                0 <= new_pos[0] < self.model.grid.width
                and 0 <= new_pos[1] < self.model.grid.height
            ):
                continue

            # Check for obstacles
            cell_contents = self.model.grid.get_cell_list_contents([new_pos])
            is_obstacle = any(
                hasattr(content, "state") and content.state == "obstacle"
                for content in cell_contents
            )

            if not is_obstacle:
                possible_moves.append(new_pos)

        return possible_moves

    def step(self):
        """Implement basic behavior"""
        if self.pos == self.home_charger and self.battery < 100:
            self.charge_battery()
            self.last_action = RoombaActions.CHARGE
            return
        if self.battery <= 20:  # If battery is low, try to return to charging station
            if self.pos == self.home_charger:
                self.charge_battery()
            else:
                # Simple movement towards charging station
                x, y = self.pos
                charge_x, charge_y = self.home_charger

                if x < charge_x and self.move((x + 1, y)):
                    self.last_action = RoombaActions.MOVE_RIGHT
                elif x > charge_x and self.move((x - 1, y)):
                    self.last_action = RoombaActions.MOVE_LEFT
                elif y < charge_y and self.move((x, y + 1)):
                    self.last_action = RoombaActions.MOVE_UP
                elif y > charge_y and self.move((x, y - 1)):
                    self.last_action = RoombaActions.MOVE_DOWN

        else:  # Normal operation
            # Try to clean current cell
            if self.clean_current_cell():
                return

            # If can't clean, try to move to a random possible position
            possible_moves = self.get_possible_moves()
            if possible_moves:
                new_pos = self.random.choice(possible_moves)
                if self.move(new_pos):
                    # Update last action based on movement direction
                    x_diff = new_pos[0] - self.pos[0]
                    y_diff = new_pos[1] - self.pos[1]
                    if x_diff > 0:
                        self.last_action = RoombaActions.MOVE_RIGHT
                    elif x_diff < 0:
                        self.last_action = RoombaActions.MOVE_LEFT
                    elif y_diff > 0:
                        self.last_action = RoombaActions.MOVE_UP
                    else:
                        self.last_action = RoombaActions.MOVE_DOWN
