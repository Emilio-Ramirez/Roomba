from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from src.agents.cell import Cell
from src.agents.roomba import Roomba
import random


class RoomModel(Model):
    """Model class for the Roomba simulation."""

    def __init__(
        self,
        width=10,
        height=10,
        dirty_percent=0.3,
        obstacle_percent=0.2,
        n_agents=1,
        max_time=1000,
    ):
        super().__init__()
        self.width = width
        self.height = height
        self.dirty_percent = dirty_percent
        self.obstacle_percent = obstacle_percent
        self.n_agents = n_agents
        self.max_time = max_time
        self.current_time = 0
        self.running = True

        # Métricas
        self.movements_count = 0
        self.clean_cells_count = 0
        self.initial_dirty_cells = 0

        self.grid = MultiGrid(width, height, False)
        self.schedule = RandomActivation(self)

        # Add DataCollector
        self.datacollector = DataCollector(
            model_reporters={
                "Clean_Percentage": lambda m: (
                    sum(
                        1
                        for x in range(m.width)
                        for y in range(m.height)
                        if m.grid.get_cell_list_contents([(x, y)])[0].state == "clean"
                    )
                    / (m.width * m.height)
                    * 100
                ),
                "Total_Movements": lambda m: sum(
                    roomba.movements for roomba in m.roombas
                ),
                "Time_Steps": lambda m: m.current_time,
            },
            agent_reporters={
                "Battery": lambda a: a.battery if isinstance(a, Roomba) else None,
                "Movements": lambda a: a.movements if isinstance(a, Roomba) else None,
            },
        )

        # Initialize the grid and agents
        self.init_grid()
        self.init_roombas()

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

        # Add charging station at (1,1) for single agent mode
        if self.n_agents == 1:
            cell = self.grid.get_cell_list_contents([(1, 1)])[0]
            cell.set_state("charging_station")

        # Count initial clean cells
        self.clean_cells_count = self.width * self.height

        # Calculate available positions and cells
        total_cells = self.width * self.height
        positions = [(x, y) for x in range(self.width) for y in range(self.height)]

        # Reserve charging station position for single agent
        if self.n_agents == 1:
            positions.remove((1, 1))
            total_cells -= 1  # Reduce available cells by 1 for charging station

        # Calculate number of dirty and obstacle cells
        dirty_cells = min(int(total_cells * self.dirty_percent), len(positions))

        # Place dirty cells
        if dirty_cells > 0:
            dirty_positions = random.sample(positions, dirty_cells)
            for pos in dirty_positions:
                cell = self.grid.get_cell_list_contents([pos])[0]
                cell.set_state("dirty")
                self.clean_cells_count -= 1
                positions.remove(pos)  # Remove used positions

            self.initial_dirty_cells = dirty_cells

        # Calculate and place obstacles in remaining positions
        remaining_cells = len(positions)
        obstacle_cells = min(int(total_cells * self.obstacle_percent), remaining_cells)

        if obstacle_cells > 0:
            # Filter positions that are still clean
            clean_positions = [
                pos
                for pos in positions
                if self.grid.get_cell_list_contents([pos])[0].state == "clean"
            ]
            # Place obstacles
            for pos in random.sample(clean_positions, obstacle_cells):
                cell = self.grid.get_cell_list_contents([pos])[0]
                cell.set_state("obstacle")
                self.clean_cells_count -= 1

    def init_roombas(self):
        """Initialize multiple Roombas with charging stations"""
        self.roombas = []

        if self.n_agents == 1:
            # Single agent starts at (1,1)
            initial_pos = (1, 1)
            # Ensure cell is a charging station
            cell = self.grid.get_cell_list_contents([initial_pos])[0]
            cell.set_state("charging_station")
            # Create roomba without initial position
            roomba = Roomba(self.next_id(), self, None)  # Initialize with None position
            self.roombas.append(roomba)
            self.schedule.add(roomba)
            self.grid.place_agent(roomba, initial_pos)
            roomba.pos = initial_pos  # Set position after placement
            roomba.home_charger = initial_pos
        else:
            # Multiple agents at random positions
            available_positions = [
                (x, y)
                for x in range(self.width)
                for y in range(self.height)
                if not any(
                    isinstance(agent, Roomba)
                    for agent in self.grid.get_cell_list_contents([(x, y)])
                )
                and self.grid.get_cell_list_contents([(x, y)])[0].state != "obstacle"
            ]

            for _ in range(self.n_agents):
                if available_positions:
                    pos = self.random.choice(available_positions)
                    available_positions.remove(pos)

                    # First set the cell as charging station
                    cell = self.grid.get_cell_list_contents([pos])[0]
                    cell.set_state("charging_station")

                    # Create roomba without initial position
                    roomba = Roomba(
                        self.next_id(), self, None
                    )  # Initialize with None position
                    self.roombas.append(roomba)
                    self.schedule.add(roomba)
                    self.grid.place_agent(roomba, pos)
                    roomba.pos = pos  # Set position after placement
                    roomba.home_charger = pos

    def get_metrics(self):
        """Return current metrics of the simulation"""
        total_cells = self.width * self.height
        clean_cells = sum(
            1
            for x in range(self.width)
            for y in range(self.height)
            if self.grid.get_cell_list_contents([(x, y)])[0].state == "clean"
        )

        total_movements = sum(roomba.movements for roomba in self.roombas)

        return {
            "time_steps": self.current_time,
            "clean_percentage": (clean_cells / total_cells) * 100,
            "total_movements": total_movements,
            "movements_per_agent": [roomba.movements for roomba in self.roombas],
        }

    def step(self):
        """Perform one step of the simulation"""
        self.schedule.step()
        self.current_time += 1
        self.datacollector.collect(self)

        # Check if simulation should end
        if self.current_time >= self.max_time:
            self.running = False
