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
    count_of_scooters = 0
    count_of_batteries = 0
    for scooter in G.nodes[current_node]['scooters']:
        if scooter['battery'] < 60:
            count_of_scooters += 1
            if remaining_batteries > 0:
                replacement_log.append((current_node, scooter['id'], scooter['battery']))
                # print("Debug: replace batteries", (current_node, scooter['id'], scooter['battery']))
                scooter['battery'] = 100
                remaining_batteries -= 1
                count_of_batteries += 1
    # print(count_of_scooters, count_of_batteries)
    return remaining_batteries, replacement_log, count_of_scooters, count_of_batteries

def find_nearest_charging_station(G, current_node, visited_stations):
    unvisited_stations = [
        n for n in G.nodes if G.nodes[n]['type'] == 'charging_station' and n not in visited_stations
    ]
    if not unvisited_stations:
        return None
    return min(unvisited_stations, key=lambda x: gb.haversine(G.nodes[current_node]['pos'], G.nodes[x]['pos']))


def find_nearest_parking_spot(G, current_node, visited_parking_spots):
    unvisited_parking_spots = [
        n for n in G.nodes if G.nodes[n]['type'] == 'parking_spot' and n not in visited_parking_spots
    ]
    if not unvisited_parking_spots:
        return None
    return min(unvisited_parking_spots, key=lambda x: haversine(G.nodes[current_node]['pos'], G.nodes[x]['pos']))


def dijkstra_path(G, start, goal, visited_parking_spots):
    # Создаем копию графа с удаленными посещенными парковками
    G_copy = G.copy()
    for node in visited_parking_spots:
        if G_copy.nodes[node]['type'] == 'parking_spot':
            G_copy.remove_node(node)

    try:
        # Пытаемся найти путь с использованием алгоритма Дейкстры
        path = nx.dijkstra_path(G_copy, start, goal)
    except nx.NetworkXNoPath:
        # Если путь не найден, строим прямой путь
        # print("Debug: no path")
        path = [start, goal]

    return path

def greedy_dijkstra_route_planning(G, start, battery_capacity=15):
    path = [start]
    remaining_batteries = battery_capacity
    current_node = start
    replacement_log = []
    visited_stations = [start]
    visited_parking_spots = set()

    G.nodes[start]['visited'] = True

    # Прямое движение до 10-й станции
    while len(visited_stations) < 10:
        nearest_charging_station = find_nearest_charging_station(G, current_node, visited_stations)
        if not nearest_charging_station:
            break

        dijkstra_path_nodes = dijkstra_path(G, current_node, nearest_charging_station, visited_parking_spots)
        del path[-1]

        for node in dijkstra_path_nodes:
            if G.nodes[node]['type'] == 'parking_spot':
                remaining_batteries, log, count_of_scooters, count_of_batteries = replace_batteries(G, node, remaining_batteries)
                replacement_log.extend(log)
                if count_of_scooters == count_of_batteries:
                    visited_parking_spots.add(node)
                    G.nodes[node]['visited'] = True
                    # print(f"Debug: {node} is visited")
            else:
                G.nodes[node]['visited'] = True
            path.append(node)


        current_node = nearest_charging_station
        visited_stations.append(current_node)
        remaining_batteries = battery_capacity

    # Обратное движение от 10-й к 1-й станции
    # print("Debug: go back")
    remaining_batteries = battery_capacity
    while len(visited_stations) > 1:
        next_station = visited_stations[-2]

        dijkstra_path_nodes = dijkstra_path(G, current_node, next_station, visited_parking_spots)
        # print("Debug: ", dijkstra_path_nodes)

        del path[-1]
        for node in dijkstra_path_nodes:
            if G.nodes[node]['type'] == 'parking_spot':
                remaining_batteries, log, count_of_scooters, count_of_batteries = replace_batteries(G, node, remaining_batteries)
                replacement_log.extend(log)
                if count_of_scooters == count_of_batteries:
                    visited_parking_spots.add(node)
                    G.nodes[node]['visited'] = True
                    # print(f"Debug: {node} is visited")
            else:
                G.nodes[node]['visited'] = True
            path.append(node)

        current_node = next_station
        remaining_batteries = battery_capacity
        visited_stations.pop()

    return path, calculate_zone_charge(G), replacement_log


def greedy_additional_routing(G, start, battery_capacity=15):
    path = []
    remaining_batteries = battery_capacity
    current_node = start
    replacement_log = []
    visited_parking_spots = set()
    visited_stations = set()

    while calculate_zone_charge(G) < 80:
        nearest_parking_spot = find_nearest_parking_spot(G, current_node, visited_parking_spots)
        if not nearest_parking_spot:
            print('debug: not nearest parking spot in greedy')
            break

        # Перемещаемся к ближайшей парковке
        current_node = nearest_parking_spot
        path.append(current_node)
        if G.nodes[current_node]['type'] == 'parking_spot':
            remaining_batteries, log, count_of_scooters, count_of_batteries = replace_batteries(G, current_node,
                                                                                                remaining_batteries)
            replacement_log.extend(log)
            if count_of_scooters == count_of_batteries:
                visited_parking_spots.add(current_node)
                G.nodes[current_node]['visited'] = True
                # print(f"Debug: {current_node} is visited")
        else:
            G.nodes[current_node]['visited'] = True

        if calculate_zone_charge(G) >= 80:
            path.append(start)
            return path, replacement_log

        if remaining_batteries == 0:
            nearest_station = find_nearest_charging_station(G, current_node, visited_stations)
            if not nearest_station:
                print('debug: not nearest charging station in greedy')
                break

            # Перемещаемся к ближайшей станции
            current_node = nearest_station
            path.append(current_node)
            remaining_batteries = battery_capacity
            visited_stations.add(current_node)

    path.append(start)
    return path, replacement_log


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


def save_path_to_file(_path, filename='route_path.txt'):
    with open(filename, 'w') as f:
        for _node in _path:
            f.write(_node + '\n')


def main_route_planning(G, G_full, start, battery_capacity=15):
    path, zone_charge, replacement_log = greedy_dijkstra_route_planning(G, start, battery_capacity)
    # print("\nReplacement Log:")
    # for log in replacement_log:
    #     print(f"Station: {log[0]}, Scooter ID: {log[1]}, Previous Battery: {log[2]}%")
    print(f"Zone Charge after Dijkstra: {zone_charge:.2f}%")
    print("paht in Dijkstra", path)
    print(f"Path distance in Dijkstra: {calculate_path_distance(G, path)}")

    if zone_charge < 80:
        path2, replacement_log = greedy_additional_routing(G, path[-1], battery_capacity)
        print("path in greedy: ", path2)
        path += path2
    return path, calculate_zone_charge(G), replacement_log


# Загрузка графа
G = nx.read_gml('graph_range.gml')
G_full = nx.read_gml('graph.gml')

print(f"Zone Charge before algo: {calculate_zone_charge(G):.2f}%")

# Инициализация всех узлов как непосещенных
for node in G.nodes:
    G.nodes[node]['visited'] = False

# Установка стартовой вершины
start_node = 'CS_0'
path, zone_charge, replacement_log = main_route_planning(G, G_full, start_node)
save_path_to_file(path)

print(f"Optimal Path: {path}")
print(f"Zone Charge: {zone_charge:.2f}%")
path_distance = calculate_path_distance(G, path)
print(f"Path Distance: {path_distance}")
# print("\nReplacement Log:")
# for log in replacement_log:
#     print(f"Station: {log[0]}, Scooter ID: {log[1]}, Previous Battery: {log[2]}%")

# Визуализация графа и маршрута
pos = nx.get_node_attributes(G, 'pos')
node_colors = ['red' if G.nodes[node]['type'] == 'charging_station' else 'blue' for node in G.nodes]

plt.figure(figsize=(15, 10))
nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=300, font_size=8)

# Выделение оптимального маршрута
if path:
    path_edges = list(zip(path, path[1:]))
    nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='green', width=2)

plt.title(f'Route from {start_node} Using Greedy Algorithm')
plt.show()
