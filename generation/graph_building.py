import csv
import networkx as nx
from math import radians, cos, sin, sqrt, atan2
import random

rng = random.SystemRandom()

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

def read_coordinates_from_csv(file_path):
    charging_stations = []
    parking_spots = []
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            coord = (float(row['latitude']), float(row['longitude']))
            if row['type'] == 'charging_station':
                charging_stations.append(coord)
            elif row['type'] == 'parking_spot':
                parking_spots.append(coord)
    return charging_stations, parking_spots

def build_base_graph(file_path):

    charging_stations, parking_spots = read_coordinates_from_csv(file_path)

    G = nx.Graph()
    for i, coord in enumerate(charging_stations):
        G.add_node(f'CS_{i}', type='charging_station', visited=False, pos=coord)
    for i, coord in enumerate(parking_spots):
        G.add_node(f'PS_{i}', type='parking_spot', scooters=[], pos=coord)
    return G

def build_range_graph(G, range=0.5):
    for node1 in G.nodes:
        for node2 in G.nodes:
            if node1 != node2 and (G.nodes[node1]['type'] == 'parking_spot' or G.nodes[node2]['type'] == 'parking_spot'):
                pos1 = G.nodes[node1]['pos']
                pos2 = G.nodes[node2]['pos']
                distance = haversine(pos1, pos2)
                if (distance <= range):
                    G.add_edge(node1, node2, weight=distance)

def build_full_graph(G):
    for node1 in G.nodes:
        for node2 in G.nodes:
            if node1 != node2:
                pos1, pos2 = G.nodes[node1]['pos'], G.nodes[node2]['pos']
                distance = haversine(pos1, pos2)
                G.add_edge(node1, node2, weight=distance)

def populate_scooters(G, total_scooters=150, min_scooters=0, max_scooters=7, average_percentage=45):
    parking_spots = [node for node, attr in G.nodes(data=True) if attr['type'] == 'parking_spot']
    num_parking_spots = len(parking_spots)
    scooters_per_parking = [min_scooters] * num_parking_spots
    remaining_scooters = total_scooters - sum(scooters_per_parking)

    for _ in range(remaining_scooters):
        spot_index = rng.randint(0, num_parking_spots - 1)
        if scooters_per_parking[spot_index] < max_scooters:
            scooters_per_parking[spot_index] += 1

    total_battery_sum = total_scooters * average_percentage
    all_scooters = []

    for i, spot in enumerate(parking_spots):
        num_scooters = scooters_per_parking[i]
        scooters = [{'id': j, 'battery': 0} for j in range(num_scooters)]
        all_scooters.extend(scooters)
        G.nodes[spot]['scooters'] = scooters

    for scooter in all_scooters:
        scooter['battery'] = rng.randint(0, 100)

    current_battery_sum = sum(scooter['battery'] for scooter in all_scooters)
    adjustment_factor = total_battery_sum / current_battery_sum

    for scooter in all_scooters:
        scooter['battery'] = round(scooter['battery'] * adjustment_factor)
    
    current_battery_sum = sum(scooter['battery'] for scooter in all_scooters)
    adjustment_needed = total_battery_sum - current_battery_sum
    if adjustment_needed != 0:
        for _ in range(abs(adjustment_needed)):
            scooter = rng.choice(all_scooters)
            if adjustment_needed > 0 and scooter['battery'] < 100:
                scooter['battery'] += 1
            elif adjustment_needed < 0 and scooter['battery'] > 0:
                scooter['battery'] -= 1

    start = 0
    for i, spot in enumerate(parking_spots):
        G.nodes[spot]['scooters'] = all_scooters[start:start + scooters_per_parking[i]]
        start += scooters_per_parking[i]

def graph_save(G, filename='../data/graph.gml'):
    nx.write_gml(G, filename)

def graph_load(filename='../data/graph.gml'):
    return nx.read_gml(filename)

def calculate_path_distance(G, path):
    total_distance = 0
    for i in range(len(path) - 1):
        if G.has_edge(path[i], path[i+1]):
            print(path[i], path[i+1], G[path[i]][path[i+1]]['weight'])
            total_distance += G[path[i]][path[i+1]]['weight']
        else:
            print(path[i], path[i+1])
            total_distance += haversine(G.nodes[path[i]]['pos'], G.nodes[path[i+1]]['pos'])
    return total_distance

G = build_base_graph(file_path='../data/dynamic_coords.csv')
populate_scooters(G, 150, 0, 10, average_percentage=45)
build_full_graph(G)
graph_save(G, '../data/graph.gml')

g = build_base_graph(file_path='../data/dynamic_coords.csv')
populate_scooters(g, 150, 0, 10, average_percentage=45)
build_range_graph(g, 0.7)
graph_save(g, '../data/graph_range.gml')
