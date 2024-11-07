from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from src.agents.cell import Cell
from src.agents.roomba import Roomba
import random


class RoomModel(Model):
    """Model class for the Roomba simulation."""

    def __init__(self, width=10, height=10, dirty_percent=0.3, obstacle_percent=0.2):
        super().__init__()
        self.width = width
        self.height = height
        self.dirty_percent = dirty_percent
        self.obstacle_percent = obstacle_percent

        self.grid = MultiGrid(width, height, False)
        self.schedule = RandomActivation(self)

        # Initialize the grid
        self.init_grid()

        # Add Roomba at charging station
        self.roomba = Roomba(self.next_id(), self, (1, 1))
        self.grid.place_agent(self.roomba, (1, 1))
        self.schedule.add(self.roomba)

    def init_grid(self):
        """Initialize the grid with cells"""
        # Create all clean cells first
        cell_id = 0
        for x in range(self.width):
            for y in range(self.height):
                cell = Cell(cell_id, self, "clean")
                self.grid.place_agent(cell, (x, y))
                self.schedule.add(cell)
                cell_id += 1

        # Add charging station at (1,1)
        cell = self.grid.get_cell_list_contents([(1, 1)])[0]
        cell.set_state("charging_station")

        # Randomly place dirty cells
        dirty_cells = int(self.width * self.height * self.dirty_percent)
        positions = [(x, y) for x in range(self.width) for y in range(self.height)]
        positions.remove((1, 1))  # Remove charging station position

        for pos in random.sample(positions, dirty_cells):
            cell = self.grid.get_cell_list_contents([pos])[0]
            cell.set_state("dirty")

        # Randomly place obstacles
        obstacle_cells = int(self.width * self.height * self.obstacle_percent)
        positions = [
            pos
            for pos in positions
            if self.grid.get_cell_list_contents([pos])[0].state == "clean"
        ]

        for pos in random.sample(positions, obstacle_cells):
            cell = self.grid.get_cell_list_contents([pos])[0]
            cell.set_state("obstacle")

    def step(self):
        self.schedule.step()
