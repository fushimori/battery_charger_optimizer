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

def build_graph():
    file_path = 'coordinates.csv'

    charging_stations, parking_spots = read_coordinates_from_csv(file_path)

    G = nx.Graph()

    for i, coord in enumerate(charging_stations):
        G.add_node(f'CS_{i}', type='charging_station', visited=False, pos=coord)

    for i, coord in enumerate(parking_spots):
        G.add_node(f'PS_{i}', type='parking_spot',  scooters=[], pos=coord)

    for node1 in G.nodes:
        for node2 in G.nodes:
            if node1 != node2:
                pos1 = G.nodes[node1]['pos']
                pos2 = G.nodes[node2]['pos']
                distance = haversine(pos1, pos2)
                G.add_edge(node1, node2, weight=distance)

    return G

def populate_scooters(G, total_scooters=150, min_scooters=0, max_scooters=7, min_percentage=0, max_percentage=100):
    parking_spots = [node for node, attr in G.nodes(data=True) if attr['type'] == 'parking_spot']
    num_parking_spots = len(parking_spots)

    scooters_per_parking = [min_scooters] * num_parking_spots
    remaining_scooters = total_scooters - sum(scooters_per_parking)
    
    for _ in range(remaining_scooters):
        spot_index = rng.randint(0, num_parking_spots - 1)
        if scooters_per_parking[spot_index] < max_scooters:
            scooters_per_parking[spot_index] += 1
    
    for i, spot in enumerate(parking_spots):
        #print(f"Populating parking spot {spot} with {scooters_per_parking[i]} scooters")
        scooters = [{'id': j, 'battery': rng.randint(min_percentage, max_percentage)} for j in range(scooters_per_parking[i])]
        G.nodes[spot]['scooters'] = scooters

    # all_scooters_battery = [scooter['battery'] for spot in parking_spots for scooter in G.nodes[spot]['scooters']]
    # return all_scooters_battery

def graph_save(G):
    nx.write_gml(G, 'graph.gml')

def graph_load():
    return nx.read_gml('graph.gml')

G = build_graph()
populate_scooters(G, 150, 0, 10, 0, 100)
graph_save(G)

# scooters = populate_scooters(G, 150, 0, 10, 0, 100)
# 

