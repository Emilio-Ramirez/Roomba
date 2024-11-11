from src.model.room import RoomModel
from mesa.datacollection import DataCollector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def run_simulation_batch(
    width=10,
    height=10,
    n_agents=1,
    dirty_percent=0.3,
    obstacle_percent=0.2,
    max_time=1000,
    n_simulations=5,
):
    """Run multiple simulations with the same parameters and collect detailed statistics"""
    detailed_results = []
    
    print(f"\nRunning {n_simulations} simulations with {n_agents} agent(s):")
    print("=" * 50)
    
    for i in range(n_simulations):
        print(f"\nSimulation {i+1}:")
        print("-" * 30)
        
        # Initialize model
        model = RoomModel(
            width=width,
            height=height,
            n_agents=n_agents,
            dirty_percent=dirty_percent,
            obstacle_percent=obstacle_percent,
            max_time=max_time,
        )
        
        # Store time series data
        time_series = {
            "Clean_Percentage": [],
            "Total_Movements": [],
            "Average_Battery": [],
            "Explored_Cells_Percentage": [],
            "Cleaned_Cells_Percentage": [],
            "Cleaning_Efficiency": [],
            "Battery_Efficiency": [],
        }
        
        # Run simulation
        while model.current_time < max_time and model.running:
            model.step()
            
            # Collect data at each step
            clean_percentage = sum(
                1 for x in range(model.width) for y in range(model.height)
                if model.grid.get_cell_list_contents([(x, y)])[0].state == "clean"
            ) / (model.width * model.height) * 100
            
            total_movements = sum(roomba.movements for roomba in model.roombas)
            avg_battery = sum(roomba.battery for roomba in model.roombas) / len(model.roombas)
            explored_cells = sum(len(roomba.explored_cells) for roomba in model.roombas)
            explored_percentage = (explored_cells / (model.width * model.height)) * 100
            cleaned_percentage = (model.clean_cells_count / (model.width * model.height)) * 100
            
            # Calculate efficiencies
            cleaning_efficiency = (model.clean_cells_count / max(total_movements, 1)) * 100
            battery_used = sum(100 - roomba.battery for roomba in model.roombas)
            battery_efficiency = (model.clean_cells_count / max(battery_used, 1)) * 100
            
            # Store in time series
            time_series["Clean_Percentage"].append(clean_percentage)
            time_series["Total_Movements"].append(total_movements)
            time_series["Average_Battery"].append(avg_battery)
            time_series["Explored_Cells_Percentage"].append(explored_percentage)
            time_series["Cleaned_Cells_Percentage"].append(cleaned_percentage)
            time_series["Cleaning_Efficiency"].append(cleaning_efficiency)
            time_series["Battery_Efficiency"].append(battery_efficiency)
        
        # Calculate final metrics
        final_metrics = {
            "time_steps": model.current_time,
            "clean_percentage": clean_percentage,
            "total_movements": total_movements,
            "average_battery": avg_battery,
            "explored_percentage": explored_percentage,
            "cleaned_percentage": cleaned_percentage,
            "cleaning_efficiency": cleaning_efficiency,
            "battery_efficiency": battery_efficiency,
            "time_series": time_series
        }
        
        detailed_results.append(final_metrics)
        
        # Print detailed results for this simulation
        print(f"Time steps: {final_metrics['time_steps']}")
        print(f"Final clean percentage: {final_metrics['clean_percentage']:.2f}%")
        print(f"Total movements: {final_metrics['total_movements']}")
        print(f"Final average battery: {final_metrics['average_battery']:.2f}%")
        print(f"Explored area: {final_metrics['explored_percentage']:.2f}%")
        print(f"Cleaned area: {final_metrics['cleaned_percentage']:.2f}%")
        print(f"Cleaning efficiency: {final_metrics['cleaning_efficiency']:.2f}%")
        print(f"Battery efficiency: {final_metrics['battery_efficiency']:.2f}%")
        
    return detailed_results

def analyze_results(results):
    """Analyze the results of multiple simulations with detailed statistics"""
    analysis = {
        "average_time_steps": sum(r["time_steps"] for r in results) / len(results),
        "average_clean_percentage": sum(r["clean_percentage"] for r in results) / len(results),
        "average_movements": sum(r["total_movements"] for r in results) / len(results),
        "average_battery": sum(r["average_battery"] for r in results) / len(results),
        "average_explored": sum(r["explored_percentage"] for r in results) / len(results),
        "average_cleaned": sum(r["cleaned_percentage"] for r in results) / len(results),
        "average_cleaning_efficiency": sum(r["cleaning_efficiency"] for r in results) / len(results),
        "average_battery_efficiency": sum(r["battery_efficiency"] for r in results) / len(results),
        "number_of_simulations": len(results),
    }
    
    # Calculate standard deviations
    analysis["std_time_steps"] = np.std([r["time_steps"] for r in results])
    analysis["std_clean_percentage"] = np.std([r["clean_percentage"] for r in results])
    analysis["std_movements"] = np.std([r["total_movements"] for r in results])
    analysis["std_battery"] = np.std([r["average_battery"] for r in results])
    analysis["std_explored"] = np.std([r["explored_percentage"] for r in results])
    analysis["std_cleaned"] = np.std([r["cleaned_percentage"] for r in results])
    analysis["std_cleaning_efficiency"] = np.std([r["cleaning_efficiency"] for r in results])
    analysis["std_battery_efficiency"] = np.std([r["battery_efficiency"] for r in results])
    
    return analysis

def plot_results(single_results, multi_results):
    """Create comprehensive comparative plots of the simulation results"""
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    fig.suptitle('Single Agent vs Multiple Agents Performance Comparison')
    
    # Prepare data for all metrics
    metrics = [
        ("clean_percentage", "Clean Percentage (%)"),
        ("time_steps", "Time Steps"),
        ("total_movements", "Total Movements"),
        ("average_battery", "Average Battery (%)"),
        ("explored_percentage", "Explored Area (%)"),
        ("cleaned_percentage", "Cleaned Area (%)"),
        ("cleaning_efficiency", "Cleaning Efficiency (%)"),
        ("battery_efficiency", "Battery Efficiency (%)")
    ]
    
    for idx, (metric, title) in enumerate(metrics):
        ax = axes[idx // 4, idx % 4]
        single_data = [r[metric] for r in single_results]
        multi_data = [r[metric] for r in multi_results]
        
        ax.boxplot([single_data, multi_data], labels=["Single Agent", "Multiple Agents"])
        ax.set_title(title)
        ax.set_ylabel("Value")
        ax.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Run simulations with single agent
    print("\nRunning single agent simulations...")
    single_agent_results = run_simulation_batch(n_agents=1)
    single_analysis = analyze_results(single_agent_results)
    
    print("\nSingle Agent Analysis:")
    print("=" * 50)
    print(f"Average time steps: {single_analysis['average_time_steps']:.2f} ± {single_analysis['std_time_steps']:.2f}")
    print(f"Average clean percentage: {single_analysis['average_clean_percentage']:.2f}% ± {single_analysis['std_clean_percentage']:.2f}%")
    print(f"Average movements: {single_analysis['average_movements']:.2f} ± {single_analysis['std_movements']:.2f}")
    print(f"Average battery level: {single_analysis['average_battery']:.2f}% ± {single_analysis['std_battery']:.2f}%")
    print(f"Average explored area: {single_analysis['average_explored']:.2f}% ± {single_analysis['std_explored']:.2f}%")
    print(f"Average cleaned area: {single_analysis['average_cleaned']:.2f}% ± {single_analysis['std_cleaned']:.2f}%")
    print(f"Average cleaning efficiency: {single_analysis['average_cleaning_efficiency']:.2f}% ± {single_analysis['std_cleaning_efficiency']:.2f}%")
    print(f"Average battery efficiency: {single_analysis['average_battery_efficiency']:.2f}% ± {single_analysis['std_battery_efficiency']:.2f}%")
    
    # Run simulations with multiple agents
    print("\nRunning multiple agent simulations...")
    multi_agent_results = run_simulation_batch(n_agents=3)
    multi_analysis = analyze_results(multi_agent_results)
    
    print("\nMultiple Agents Analysis:")
    print("=" * 50)
    print(f"Average time steps: {multi_analysis['average_time_steps']:.2f} ± {multi_analysis['std_time_steps']:.2f}")
    print(f"Average clean percentage: {multi_analysis['average_clean_percentage']:.2f}% ± {multi_analysis['std_clean_percentage']:.2f}%")
    print(f"Average movements: {multi_analysis['average_movements']:.2f} ± {multi_analysis['std_movements']:.2f}")
    print(f"Average battery level: {multi_analysis['average_battery']:.2f}% ± {multi_analysis['std_battery']:.2f}%")
    print(f"Average explored area: {multi_analysis['average_explored']:.2f}% ± {multi_analysis['std_explored']:.2f}%")
    print(f"Average cleaned area: {multi_analysis['average_cleaned']:.2f}% ± {multi_analysis['std_cleaned']:.2f}%")
    print(f"Average cleaning efficiency: {multi_analysis['average_cleaning_efficiency']:.2f}% ± {multi_analysis['std_cleaning_efficiency']:.2f}%")
    print(f"Average battery efficiency: {multi_analysis['average_battery_efficiency']:.2f}% ± {multi_analysis['std_battery_efficiency']:.2f}%")
    
    # Plot comparative results
    plot_results(single_agent_results, multi_agent_results)
