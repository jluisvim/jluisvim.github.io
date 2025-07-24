import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pyswip import Prolog
import random
import math
import numpy as np
from collections import defaultdict
from sklearn.cluster import DBSCAN  # For sub-swarm detection

# Configuration
NUM_AGENTS = 30
WORLD_SIZE = 50
NEIGHBOR_RADIUS = 10
ENERGY_DECAY = 0.05  # Energy lost per step
DEBUG = True
METRICS = True

# Initialize Prolog
prolog = Prolog()
prolog.consult("agents.pl")

# Agent setup
agent_colors = plt.cm.tab20(np.linspace(0, 1, NUM_AGENTS))
positions_history = defaultdict(list)

# Initialize agents with energy
for i in range(NUM_AGENTS):
    x = random.uniform(5, WORLD_SIZE-5)
    y = random.uniform(5, WORLD_SIZE-5)
    vx = random.uniform(-1, 1)
    vy = random.uniform(-1, 1)
    prolog.assertz(f"posicion({i}, {x}, {y})")
    prolog.assertz(f"velocidad({i}, {vx}, {vy})")
    prolog.assertz(f"energia({i}, 100.0)")  # Starting energy
    positions_history[i].append((x, y))

def calculate_structural_resilience(positions, neighbor_radius):
    """Measure connectivity and fragmentation resistance using graph theory"""
    positions = np.array(positions)
    n_agents = len(positions)
    
    # Adjacency matrix
    dist_matrix = np.linalg.norm(positions[:, None] - positions, axis=2)
    adj_matrix = (dist_matrix < neighbor_radius).astype(int)
    np.fill_diagonal(adj_matrix, 0)
    
    # Graph metrics
    degree_centrality = np.mean(np.sum(adj_matrix, axis=1))
    clustering_coeff = np.mean([np.sum(adj_matrix[i] @ adj_matrix[:, i]) / 
                             (np.sum(adj_matrix[i])**2) 
                             for i in range(n_agents) if np.sum(adj_matrix[i]) > 1])
    
    # Simulate node removal (attack/failure)
    random_agent = np.random.randint(n_agents)
    adj_matrix_removed = np.delete(np.delete(adj_matrix, random_agent, 0), random_agent, 1)
    remaining_edges = np.sum(adj_matrix_removed) / 2
    
    resilience_score = 0.4 * degree_centrality + 0.3 * clustering_coeff + 0.3 * (remaining_edges / n_agents)
    return resilience_score

def calculate_energy_resilience(energies, decay_rate):
    """Quantify energy buffer and distribution health"""
    avg_energy = np.mean(energies)
    energy_std = np.std(energies)
    min_energy = np.min(energies)
    
    # Time-to-collapse estimation (steps until first agent dies)
    ttc = min_energy / decay_rate if decay_rate > 0 else float('inf')
    
    resilience_score = 0.6 * (avg_energy / 100) + 0.2 * (1 - energy_std/50) + 0.2 * (ttc / 100)
    return resilience_score

def calculate_adaptive_capacity(prev_positions, current_positions):
    """Measure response to perturbations using trajectory analysis"""
    displacements = np.linalg.norm(np.array(current_positions) - np.array(prev_positions), axis=1)
    avg_speed = np.mean(displacements)
    speed_variance = np.var(displacements)
    
    # Diversity of motion (0=homogeneous, 1=heterogeneous)
    motion_diversity = min(speed_variance / (avg_speed + 1e-6), 1.0)
    
    resilience_score = 0.7 * avg_speed + 0.3 * motion_diversity
    return resilience_score

def calculate_overall_resilience(positions, energies, decay_rate, prev_positions=None):
    structural = calculate_structural_resilience(positions, NEIGHBOR_RADIUS)
    energy = calculate_energy_resilience(energies, decay_rate)
    adaptive = calculate_adaptive_capacity(prev_positions, positions) if prev_positions else 0.5
    
    # Weighted sum (adjust weights based on priorities)
    overall_resilience = 0.4 * structural + 0.4 * energy + 0.2 * adaptive
    return {
        'overall': overall_resilience,
        'structural': structural,
        'energy': energy,
        'adaptive': adaptive
    }

def calculate_swarm_metrics(positions):
    """Compute cohesion, separation, and DBSCAN clusters."""
    positions = np.array(positions)
    centroid = np.mean(positions, axis=0)
    
    # Cohesion and Separation
    distances_to_centroid = np.linalg.norm(positions - centroid, axis=1)
    cohesion = np.mean(distances_to_centroid)
    
    dist_matrix = np.linalg.norm(positions[:, None] - positions, axis=2)
    np.fill_diagonal(dist_matrix, np.inf)
    separation = np.mean(np.min(dist_matrix, axis=1))
    
    # DBSCAN Clustering
    clustering = DBSCAN(eps=NEIGHBOR_RADIUS*1.5, min_samples=2).fit(positions)
    unique_clusters = set(clustering.labels_)
    n_clusters = len(unique_clusters) - (1 if -1 in unique_clusters else 0)  # Ignore noise
    
    return cohesion, separation, n_clusters

def update(frame):
    plt.clf()
    x, y, ids, energies = [], [], [], []
    prev_positions = [positions_history[i][-1] if positions_history[i] else None 
                     for i in range(NUM_AGENTS)]
    
    # --- Energy Management ---
    for i in range(NUM_AGENTS):
        # Apply energy decay
        list(prolog.query(f"decay_energy({i}, {ENERGY_DECAY})"))
        e = float(list(prolog.query(f"energia({i}, E)"))[0]["E"])
        energies.append(e)
        
        # Die if energy depleted (optional)
        if e <= 0:
            list(prolog.query(f"retractall(posicion({i}, _, _))"))
            list(prolog.query(f"retractall(velocidad({i}, _, _))"))
            if DEBUG:
                print(f"⚰️ Agent {i} died (energy={e:.1f})")

    # --- Neighbor Detection ---
    neighbor_counts = defaultdict(int)
    for i in range(NUM_AGENTS):
        list(prolog.query(f"retractall(vecino({i}, _, _))"))
        try:
            neighbors = list(prolog.query(
                f"posicion({i}, X1, Y1), posicion(J, X2, Y2), "
                f"J \\= {i}, Dist is sqrt((X2-X1)^2 + (Y2-Y1)^2), "
                f"Dist < {NEIGHBOR_RADIUS}, J < {NUM_AGENTS}"  # Safety check
            ))
            for n in neighbors:
                prolog.assertz(f"vecino({i}, {n['J']}, {n['Dist']})")
                neighbor_counts[i] += 1
        except Exception as e:
            if DEBUG:
                print(f"⚠️ Neighbor detection error for Agent {i}: {str(e)}")

    # --- Movement Update ---
    active_agents = 0
    for i in range(NUM_AGENTS):
        try:
            pos = list(prolog.query(f"posicion({i}, X, Y)"))
            if not pos:
                continue  # Skip dead agents
            pos = pos[0]
            vel = list(prolog.query(f"velocidad({i}, VX, VY)"))[0]
            
            # Get new velocity from Prolog rules
            new_vel = list(prolog.query(f"actualizar_direccion({i}, NewVX, NewVY)"))
            if new_vel:
                new_vx, new_vy = new_vel[0]["NewVX"], new_vel[0]["NewVY"]
                
                # Normalize and scale velocity
                speed = math.sqrt(new_vx**2 + new_vy**2)
                if speed > 0:
                    new_vx = (new_vx / speed) * 0.7
                    new_vy = (new_vy / speed) * 0.7
                
                # Update knowledge base
                list(prolog.query(f"retract(velocidad({i}, _, _))"))
                prolog.assertz(f"velocidad({i}, {new_vx}, {new_vy})")
                
                # Apply movement (with world wrapping)
                new_x = (pos["X"] + new_vx) % WORLD_SIZE
                new_y = (pos["Y"] + new_vy) % WORLD_SIZE
                list(prolog.query(f"retract(posicion({i}, _, _))"))
                prolog.assertz(f"posicion({i}, {new_x}, {new_y})")
                
                x.append(new_x)
                y.append(new_y)
                ids.append(i)
                positions_history[i].append((new_x, new_y))
                active_agents += 1
                
                if DEBUG and frame % 5 == 0 and random.random() < 0.1:  # Sample debug
                    print(f"Agent {i}: ({new_x:.1f}, {new_y:.1f}) "
                          f"v=({new_vx:.2f}, {new_vy:.2f}) "
                          f"E={energies[i]:.1f} "
                          f"N={neighbor_counts[i]}")
        except Exception as e:
            if DEBUG:
                print(f"⚠️ Movement error for Agent {i}: {str(e)}")

    # --- Resilience Calculation ---
    if x:  # Only if there are active agents
        resilience = calculate_overall_resilience(
            positions=list(zip(x, y)),
            energies=energies,
            decay_rate=ENERGY_DECAY,
            prev_positions=prev_positions
        )
        
        # DBSCAN Clustering
        positions = np.array(list(zip(x, y)))
        clustering = DBSCAN(eps=NEIGHBOR_RADIUS*1.5, min_samples=2).fit(positions)
        n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
        
        if DEBUG and frame % 10 == 0:
            print(f"\n📊 Frame {frame} Metrics:")
            print(f"  Active Agents: {active_agents}/{NUM_AGENTS}")
            print(f"  Clusters: {n_clusters}")
            print(f"  Resilience: {resilience['overall']:.2f} "
                  f"(S={resilience['structural']:.2f}, "
                  f"E={resilience['energy']:.2f}, "
                  f"A={resilience['adaptive']:.2f})")

    # --- Visualization ---
    if x:
        # Draw agents (size scaled by energy)
        sizes = [50 + 100 * (e/max(energies)) for e in energies]
        scatter = plt.scatter(x, y, c=agent_colors[:len(x)], s=sizes, alpha=0.7, edgecolors='k')
        
        # Agent labels (ID + energy)
        for i, (xi, yi) in enumerate(zip(x, y)):
            plt.text(xi+0.5, yi+0.5, f"{ids[i]}:{energies[i]:.0f}", 
                    fontsize=6, ha='center', va='center', 
                    color='white' if energies[i] < 30 else 'black')
        
        # Cluster visualization
        if METRICS:
            for cluster_id in set(clustering.labels_):
                if cluster_id != -1:
                    cluster_points = positions[clustering.labels_ == cluster_id]
                    hull = plt.Polygon(cluster_points, closed=True, fill=True, 
                                     alpha=0.05, edgecolor='gray', linestyle='--')
                    plt.gca().add_patch(hull)
        
        # Resilience indicator
        plt.text(2, 2, f"Resilience: {resilience['overall']:.2f}", 
                bbox=dict(facecolor='white', alpha=0.7), fontsize=8)
    
    plt.xlim(0, WORLD_SIZE)
    plt.ylim(0, WORLD_SIZE)
    plt.title(f"Swarm Simulation (Frame {frame})\n"
             f"Clusters: {n_clusters} | "
             f"Avg Energy: {np.mean(energies):.1f}")
    plt.grid(True, alpha=0.2)

# Run animation
fig = plt.figure(figsize=(12, 12))
ani = animation.FuncAnimation(fig, update, frames=100, interval=300)
plt.show()
