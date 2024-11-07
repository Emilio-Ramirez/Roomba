from src.visualization.server import create_server

if __name__ == "__main__":
    try:
        server = create_server()
        print(f"Starting server on port {server.port}")
        server.launch()
    except OSError as e:
        print(f"Error starting server: {e}")
        print("Try closing any running Python processes and try again.")
        sys.exit(1)
