import csv
import random
import math
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon

rng = random.SystemRandom()

# Считывание координат зоны из CSV файла
def read_zone_coordinates(file_path):
    coordinates = []
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            coordinates.append((float(row['latitude']), float(row['longitude'])))
    return coordinates

# Функция для генерации равномерно распределённых точек с использованием Poisson Disk Sampling
def poisson_disk_sampling(polygon, radius, num_points, k=30):
    min_x, min_y, max_x, max_y = polygon.bounds
    width = max_x - min_x
    height = max_y - min_y
    cell_size = radius / math.sqrt(2)
    grid_width = int(math.ceil(width / cell_size))
    grid_height = int(math.ceil(height / cell_size))

    grid = [[None for _ in range(grid_height)] for _ in range(grid_width)]
    process_list = []
    sample_points = []

    def add_point(point):
        sample_points.append(point)
        process_list.append(point)
        grid_x = int((point.x - min_x) / cell_size)
        grid_y = int((point.y - min_y) / cell_size)
        grid[grid_x][grid_y] = point

    def is_valid(point):
        if not polygon.contains(point):
            return False
        grid_x = int((point.x - min_x) / cell_size)
        grid_y = int((point.y - min_y) / cell_size)

        if grid_x < 0 or grid_x >= grid_width or grid_y < 0 or grid_y >= grid_height:
            return False

        for i in range(max(0, grid_x - 2), min(grid_width, grid_x + 3)):
            for j in range(max(0, grid_y - 2), min(grid_height, grid_y + 3)):
                neighbor = grid[i][j]
                if neighbor is not None:
                    distance = math.hypot(point.x - neighbor.x, point.y - neighbor.y)
                    if distance < radius:
                        return False
        return True

    initial_point = Point(rng.uniform(min_x, max_x), rng.uniform(min_y, max_y))
    while not polygon.contains(initial_point):
        initial_point = Point(rng.uniform(min_x, max_x), rng.uniform(min_y, max_y))
    add_point(initial_point)

    while len(sample_points) < num_points:
        if not process_list:
            break
        point = process_list.pop(rng.randint(0, len(process_list) - 1))
        for _ in range(k):  # k = 30
            angle = rng.uniform(0, 2 * math.pi)
            radius_offset = rng.uniform(radius, 2 * radius)
            new_point = Point(
                point.x + radius_offset * math.cos(angle),
                point.y + radius_offset * math.sin(angle)
            )
            if is_valid(new_point):
                add_point(new_point)
                if len(sample_points) >= num_points:
                    break

    # Добавление недостающих точек случайным образом
    while len(sample_points) < num_points:
        new_point = Point(rng.uniform(min_x, max_x), rng.uniform(min_y, max_y))

        if polygon.contains(new_point):
            add_point(new_point)

    return sample_points

# Генерация станций зарядки и парковок с использованием Poisson Disk Sampling
def generate_stations_and_parking(zone_polygon, num_charging_stations, total_parking_spots, k=500):
    radius_charging = math.sqrt(zone_polygon.area / num_charging_stations) 
    radius_parking = radius_charging / 1.05

    charging_stations = poisson_disk_sampling(zone_polygon, radius_charging, num_charging_stations, k)

    parking_spots = []
    num_parking_spots_per_station = total_parking_spots // num_charging_stations
    remaining_parking_spots = total_parking_spots % num_charging_stations

    for station in charging_stations:
        parking_polygon = station.buffer(radius_charging).intersection(zone_polygon)
        num_spots = num_parking_spots_per_station + (1 if remaining_parking_spots > 0 else 0)
        if remaining_parking_spots > 0:
            remaining_parking_spots -= 1
        parking_spots += poisson_disk_sampling(parking_polygon, radius_parking, num_spots, k)

    return charging_stations, parking_spots

# Считывание координат зоны
zone_coordinates = read_zone_coordinates('../data/zone.csv')

# Создание многоугольника зоны
zone_polygon = Polygon(zone_coordinates)

# Генерация зарядных станций и парковок
num_charging_stations = 10
total_parking_spots = 30
charging_stations, parking_spots = generate_stations_and_parking(zone_polygon, num_charging_stations, total_parking_spots)

# Запись в новый CSV файл
output_file = '../data/dynamic_coords.csv'
with open(output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['type', 'latitude', 'longitude'])
    for station in charging_stations:
        writer.writerow(['charging_station', station.x, station.y])
    for spot in parking_spots:
        writer.writerow(['parking_spot', spot.x, spot.y])

# Визуализация результата
plt.figure(figsize=(10, 10))
x, y = zip(*zone_coordinates)
plt.plot(y, x, 'r-')
plt.fill(y, x, alpha=0.3, color='gray')

for station in charging_stations:
    plt.plot(station.y, station.x, 'bo', label='Charging Station' if station == charging_stations[0] else "")

for spot in parking_spots:
    plt.plot(spot.y, spot.x, 'go', label='Parking Spot' if spot == parking_spots[0] else "")

plt.legend()
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Generated Charging Stations and Parking Spots')
plt.show()
