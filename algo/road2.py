import requests
import networkx as nx
import plotly.graph_objs as go
import plotly.io as pio
import webbrowser

# Загрузка координат из файла
def load_path_from_file(filename='route_path.txt'):
    with open(filename, 'r') as f:
        return [line.strip() for line in f]

# Получение координат узлов
def get_coordinates(G, node):
    return G.nodes[node]['pos']

def add_marker(markers_dict, location, popup_text):
    loc_tuple = tuple(location)
    if loc_tuple in markers_dict:
        markers_dict[loc_tuple] += f", {popup_text}"
    else:
        markers_dict[loc_tuple] = popup_text

# Загрузка графа
G = nx.read_gml('graph_range.gml')

path = load_path_from_file()
route_coords = [get_coordinates(G, node) for node in path]

# Формирование URL для запроса к OSRM
base_url = 'http://router.project-osrm.org/route/v1/driving/'
coords_str = ';'.join([f'{lon},{lat}' for lat, lon in route_coords])
url = f'{base_url}{coords_str}?overview=full&geometries=geojson'

# Отправка запроса к OSRM
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    route = data['routes'][0]['geometry']['coordinates']
    route_lat_lon = [(lat, lon) for lon, lat in route]
else:
    print('Error:', response.status_code, response.text)
    route_lat_lon = []

markers_dict = {}
# Формирование меток для каждой точки маршрута
add_marker(markers_dict, [route_coords[0][0], route_coords[0][1]], 'Start')
for i in range(1, len(route_coords) - 1):
    add_marker(markers_dict, [route_coords[i][0], route_coords[i][1]], str(i))
    # print(markers_dict)
add_marker(markers_dict, [route_coords[-1][0], route_coords[-1][1]], 'End')

labels = []
double_route_coords = []
for x in markers_dict:
    labels.append(markers_dict[x])
    double_route_coords.append(x)

# print(labels)
# print(route_coords)
# print(labels[22], route_coords[22])
route_coords = double_route_coords[:]

# Создание интерактивной карты с Plotly
if route_lat_lon:
    fig = go.Figure(go.Scattermapbox(
        mode="lines",
        lon=[lon for lat, lon in route_lat_lon],
        lat=[lat for lat, lon in route_lat_lon],
        line={'width': 4.5, 'color': 'blue'}))

    # Добавление меток начальной, конечной и всех промежуточных точек маршрута
    fig.add_trace(go.Scattermapbox(
        mode="markers+text",
        lon=[lon for lat, lon in route_coords],
        lat=[lat for lat, lon in route_coords],
        marker={'size': 15, 'symbol': 'circle', 'color': 'red'},
        text=[labels[i] for i in range(len(labels))],
        textposition="top right",
        textfont=dict(size=14, color="black")))

    # Настройка карты
    fig.update_layout(
        mapbox={
            'style': "open-street-map",
            'center': {'lon': route_coords[0][1], 'lat': route_coords[0][0]},
            'zoom': 14},
        showlegend=False,
        # width=1500,  # ширина фигуры
        # height=800,  # высота фигуры
    )


    # Сохранение карты в HTML-файл
    html_file = 'route_map.html'
    pio.write_html(fig, file=html_file, auto_open=False)

    # Открытие HTML-файла в браузере
    webbrowser.open_new_tab(html_file)
else:
    print("Маршрут не найден.")
