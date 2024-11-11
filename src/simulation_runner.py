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
    """Run multiple simulations with the same parameters and collect statistics"""
    results = []

    for i in range(n_simulations):
        model = RoomModel(
            width=width,
            height=height,
            n_agents=n_agents,
            dirty_percent=dirty_percent,
            obstacle_percent=obstacle_percent,
            max_time=max_time,
        )

        while model.current_time < max_time and model.running:
            model.step()

        metrics = model.get_metrics()
        results.append(metrics)

        print(f"Simulation {i+1} completed:")
        print(f"Time steps: {metrics['time_steps']}")
        print(f"Clean percentage: {metrics['clean_percentage']:.2f}%")
        print(f"Total movements: {metrics['total_movements']}")
        print("---")

    return results


def analyze_results(results):
    """Analyze the results of multiple simulations"""
    avg_time = sum(r["time_steps"] for r in results) / len(results)
    avg_clean = sum(r["clean_percentage"] for r in results) / len(results)
    avg_movements = sum(r["total_movements"] for r in results) / len(results)

    return {
        "average_time_steps": avg_time,
        "average_clean_percentage": avg_clean,
        "average_movements": avg_movements,
        "number_of_simulations": len(results),
    }


def plot_results(single_results, multi_results):
    """Create comparative plots of the simulation results"""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

    # Prepare data
    single_clean = [r["clean_percentage"] for r in single_results]
    multi_clean = [r["clean_percentage"] for r in multi_results]
    single_time = [r["time_steps"] for r in single_results]
    multi_time = [r["time_steps"] for r in multi_results]
    single_moves = [r["total_movements"] for r in single_results]
    multi_moves = [r["total_movements"] for r in multi_results]

    # Plot Clean Percentage
    ax1.boxplot([single_clean, multi_clean], labels=["Single Agent", "Multiple Agents"])
    ax1.set_title("Clean Percentage Distribution")
    ax1.set_ylabel("Percentage")

    # Plot Time Steps
    ax2.boxplot([single_time, multi_time], labels=["Single Agent", "Multiple Agents"])
    ax2.set_title("Time Steps Distribution")
    ax2.set_ylabel("Steps")

    # Plot Movements
    ax3.boxplot([single_moves, multi_moves], labels=["Single Agent", "Multiple Agents"])
    ax3.set_title("Total Movements Distribution")
    ax3.set_ylabel("Movements")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Run simulations with single agent
    print("Running single agent simulations...")
    single_agent_results = run_simulation_batch(n_agents=1)
    single_analysis = analyze_results(single_agent_results)

    print("\nSingle Agent Analysis:")
    print(f"Average time steps: {single_analysis['average_time_steps']:.2f}")
    print(
        f"Average clean percentage: {single_analysis['average_clean_percentage']:.2f}%"
    )
    print(f"Average movements: {single_analysis['average_movements']:.2f}")

    # Run simulations with multiple agents
    print("\nRunning multiple agent simulations...")
    multi_agent_results = run_simulation_batch(n_agents=3)
    multi_analysis = analyze_results(multi_agent_results)

    print("\nMultiple Agents Analysis:")
    print(f"Average time steps: {multi_analysis['average_time_steps']:.2f}")
    print(
        f"Average clean percentage: {multi_analysis['average_clean_percentage']:.2f}%"
    )
    print(f"Average movements: {multi_analysis['average_movements']:.2f}")

    # Plot comparative results
    plot_results(single_agent_results, multi_agent_results)
