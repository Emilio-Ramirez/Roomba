from mesa import Agent

class Cell(Agent):
    """A cell in the grid that can be in different states"""
    
    def __init__(self, unique_id, model, state="clean"):
        """
        Create a new cell
        States: "clean", "dirty", "obstacle", "charging_station"
        """
        super().__init__(unique_id, model)
        self.state = state
        
    def get_state(self):
        return self.state
    
    def set_state(self, new_state):
        if new_state in ["clean", "dirty", "obstacle", "charging_station"]:
            self.state = new_state
