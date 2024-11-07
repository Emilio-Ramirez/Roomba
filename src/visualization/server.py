from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from src.model.room import RoomModel
from src.agents.roomba import Roomba  # Make sure to import Roomba
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
    else:  # Cell agent
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
    # Create canvas element - just create one grid with agent_portrayal
    grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)

    # Find an available port
    port = find_free_port()
    if port is None:
        print(
            "Could not find an available port. Please close other running servers and try again."
        )
        sys.exit(1)

    # Create server
    server = ModularServer(
        RoomModel,
        [grid],
        "Roomba Environment",
        {"width": 10, "height": 10, "dirty_percent": 0.3, "obstacle_percent": 0.2},
    )

    server.port = port
    return server
