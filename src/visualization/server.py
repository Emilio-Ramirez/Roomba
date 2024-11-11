from mesa.visualization.modules import CanvasGrid, ChartModule, PieChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import Slider
from src.model.room import RoomModel
from src.agents.roomba import Roomba
import socket
import sys

def agent_portrayal(agent):
    """Single portrayal function to handle both Cell and Roomba agents"""
    if agent is None:
        return
    if isinstance(agent, Roomba):
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Layer": 1,
            "Color": "red",
            "r": 0.8,
            "text": f"{agent.battery}%",
            "text_color": "white",
        }
    else:  
        portrayal = {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Layer": 0}
        colors = {
            "clean": "white",
            "dirty": "brown",
            "obstacle": "gray",
            "charging_station": "yellow",
        }
        portrayal["Color"] = colors[agent.state]
    return portrayal

def find_free_port():
    """Find a free port to run the server"""
    ports_to_try = [8521, 8522, 8523, 8524, 8525]
    for port in ports_to_try:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("", port))
            s.close()
            return port
        except OSError:
            continue
    return None

def create_server():
    GRID_SIZE = 10
    
    grid = CanvasGrid(agent_portrayal, GRID_SIZE, GRID_SIZE)
    
    # Primera gráfica: Limpieza y Movimientos
    clean_chart = ChartModule([
        {"Label": "Clean_Percentage", "Color": "#00CC00"},
        {"Label": "Total_Movements", "Color": "#CC0000"},
    ])

    # Segunda gráfica: Nivel de batería
    battery_chart = ChartModule([
        {"Label": "Average_Battery", "Color": "#0000FF"},
    ])

    # Tercera gráfica: Exploración vs Limpieza
    exploration_chart = ChartModule([
        {"Label": "Explored_Cells_Percentage", "Color": "#FF6600"},
        {"Label": "Cleaned_Cells_Percentage", "Color": "#9933FF"},
    ])

    # Cuarta gráfica: Eficiencia de limpieza
    efficiency_chart = ChartModule([
        {"Label": "Cleaning_Efficiency", "Color": "#FF0099"},
        {"Label": "Battery_Efficiency", "Color": "#33CC33"},
    ])
    
    model_params = {
        "width": GRID_SIZE,
        "height": GRID_SIZE,
        "n_agents": Slider("Number of Roombas", 1, 1, 5, 1),
        "dirty_percent": Slider("Initial Dirty Cells", 0.3, 0.0, 1.0, 0.05),
        "obstacle_percent": Slider("Obstacle Percentage", 0.2, 0.0, 0.5, 0.05),
        "max_time": Slider("Maximum Time Steps", 1000, 100, 2000, 100),
    }

    port = find_free_port()
    if port is None:
        print("Could not find an available port. Please close other running servers and try again.")
        sys.exit(1)

    server = ModularServer(
        RoomModel,
        [grid, clean_chart, battery_chart, exploration_chart, efficiency_chart],
        "Roomba Cleaning Simulation",
        model_params,
    )
    server.port = port
    return server
