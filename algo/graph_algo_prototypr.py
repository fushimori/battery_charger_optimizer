import networkx as nx
import matplotlib.pyplot as plt
from math import radians, cos, sin, sqrt, atan2
import graph_building as gb


def haversine(coord1, coord2):
    R = 6371.0
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


def calculate_zone_charge(G):
    total_battery = 0
    scooter_count = 0
    for node in G.nodes:
        if G.nodes[node]['type'] == 'parking_spot':
            for scooter in G.nodes[node]['scooters']:
                total_battery += scooter['battery']
                scooter_count += 1
    return total_battery / scooter_count if scooter_count else 0

def replace_batteries(G, current_node, remaining_batteries):
    replacement_log = []
    for scooter in G.nodes[current_node]['scooters']:
        if scooter['battery'] < 60 and remaining_batteries > 0:
            replacement_log.append((current_node, scooter['id'], scooter['battery']))
            scooter['battery'] = 100 
            remaining_batteries -= 1
    return remaining_batteries, replacement_log

def find_nearest_charging_station(G, current_node):
    nearest_charging_station = min(
        (n for n in G.nodes if G.nodes[n]['type'] == 'charging_station' and not G.nodes[n]['visited']),
        key=lambda x: gb.haversine(G.nodes[current_node]['pos'], G.nodes[x]['pos']),
        default=None
    )
    return nearest_charging_station

def greedy_route_planning(G, start, battery_capacity=15):
    path = [start]
    remaining_batteries = battery_capacity
    current_node = start
    replacement_log = []

    G.nodes[start]['visited'] = True

    while True:
        if remaining_batteries == 0:
            nearest_charging_station = find_nearest_charging_station(G, current_node)
            if not nearest_charging_station:
                break
            path.append(nearest_charging_station)
            remaining_batteries = battery_capacity
            G.nodes[nearest_charging_station]['visited'] = True
            current_node = nearest_charging_station
            continue

        potential_parking_spots = [
            n for n in G.nodes if G.nodes[n]['type'] == 'parking_spot' and n not in path
        ]

        if not potential_parking_spots:
            break

        next_node = max(
            potential_parking_spots,
            key=lambda x: sum(1 for scooter in G.nodes[x]['scooters'] if scooter['battery'] < 50)
        )

        if next_node in path:
            break

        remaining_batteries, log = replace_batteries(G, next_node, remaining_batteries)
        replacement_log.extend(log)

        path.append(next_node)
        current_node = next_node

        zone_charge = calculate_zone_charge(G)
        if zone_charge >= 80:
            path.append(start)  # Return to the start node
            break

    return path, calculate_zone_charge(G), replacement_log

def calculate_path_distance(G, path):
    total_distance = 0
    for i in range(len(path) - 1):
        if G.has_edge(path[i], path[i+1]):
            # print(path[i], path[i+1], G[path[i]][path[i+1]]['weight'])
            total_distance += G[path[i]][path[i+1]]['weight']
        else:
            # print(path[i], path[i+1])
            total_distance += haversine(G.nodes[path[i]]['pos'], G.nodes[path[i+1]]['pos'])
    return total_distance

# Load the graph
G = nx.read_gml('graph.gml')

# Set the starting node
start_node = 'CS_0'
path, zone_charge, replacement_log = greedy_route_planning(G, start_node)

print(f"Optimal Path: {path}")
print(f"Zone Charge: {zone_charge:.2f}%")
path_distance = calculate_path_distance(G, path)
print(f"Path Distance: {path_distance}")
# print("\nReplacement Log:")
# for log in replacement_log:
#     print(f"Station: {log[0]}, Scooter ID: {log[1]}, Previous Battery: {log[2]}%")

# Visualize the graph and the route
pos = nx.get_node_attributes(G, 'pos')
node_colors = ['red' if G.nodes[node]['type'] == 'charging_station' else 'blue' for node in G.nodes]

plt.figure(figsize=(15, 10))
nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=300, font_size=8)

# Highlight the optimal path
if path:
    path_edges = list(zip(path, path[1:]))
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='green', width=2)

plt.title(f'Route from {start_node} Using Greedy Algorithm')
plt.show()
