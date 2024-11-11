from src.visualization.server import create_server
from src.simulation_runner import run_simulation_batch, analyze_results, plot_results

if __name__ == "__main__":

    # Create and start the visualization server first
    server = create_server()
    print(f"Starting visualization server on port {server.port}")
    server.launch(open_browser=True)  # This will open the browser automatically
    

    # The simulation batch analysis can run in parallel
    print("Running simulations...")
    # Single agent simulations
    single_agent_results = run_simulation_batch(n_agents=1)
    single_analysis = analyze_results(single_agent_results)
    
    # Multiple agent simulations
    multi_agent_results = run_simulation_batch(n_agents=3)
    multi_analysis = analyze_results(multi_agent_results)
    
    # Show comparative results
    plot_results(single_agent_results, multi_agent_results)
