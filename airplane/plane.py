import math, heapq, json
from decimal import Decimal

class City:
    def __init__(self, name: str, lat: float, lon: float, has_fuel: bool):
        self.name = name
        self.lat = Decimal(str(lat))
        self.lon = Decimal(str(lon))
        self.has_fuel = has_fuel
        self.time_full_tank = Decimal("0.5")


class Plane:
    def __init__(self):
        self.tank_capacity = Decimal("16000")
        self.base_fuel = Decimal("2.7")
        self.cruise_speed = Decimal("841")
        self.empty_mass = Decimal("30000")

    def get_mass(self, fuel_current: Decimal):
        density_fuel = Decimal("800")
        fuel_current_mass = fuel_current * density_fuel
        mass = self.empty_mass + fuel_current_mass
        return mass

    def get_speed(self, fuel_current: Decimal):
        speed = self.cruise_speed * (Decimal("1") - Decimal("0.10") * (fuel_current / self.tank_capacity))
        return speed


class Flight:
    def __init__(self, city1: City, city2: City, plane: Plane, wind_speed, wind_direction):
        self.city1 = city1
        self.city2 = city2
        self.plane = plane
        self.distance = self.haversine()
        self.azimuth = self.get_azimuth()
        self.wind_speed = wind_speed
        self.wind_direction = math.radians(wind_direction)
        self.dir_diff = Decimal(str(math.cos(self.get_dir_diff())))


    def haversine(self):
        R = 6371.0
        lat2 = self.city2.lat
        lon2 = self.city2.lon
        lat1 = self.city1.lat
        lon1 = self.city1.lon
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return Decimal(str(R * c))

    def get_azimuth(self) -> float:
        lat1 = math.radians(float(self.city1.lat))
        lat2 = math.radians(float(self.city2.lat))
        dlon = math.radians(float(self.city2.lon - self.city1.lon))

        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

        return math.atan2(y, x)

    def get_dir_diff(self):
        dir_diff = self.azimuth - self.wind_direction
        return dir_diff

    def get_effective_speed(self, fuel_current: Decimal):
        speed_multiplier = Decimal("1") + Decimal("0.05") * self.dir_diff
        effective = self.plane.get_speed(fuel_current) * speed_multiplier
        return effective

    def fuel_spent(self, fuel_current: Decimal):
        mass_factor = Decimal("1") + Decimal("0.30") * (fuel_current / self.plane.tank_capacity)
        wind_factor = Decimal("1") + Decimal("0.20") * (Decimal("1") - self.dir_diff)
        fuel_rate = self.plane.base_fuel * mass_factor * wind_factor
        fuel = fuel_rate * self.distance
        if fuel > fuel_current:
            return None
        return fuel

    def time(self, fuel_current: Decimal):
        v_effective = self.get_effective_speed(fuel_current)
        fuel_spent = self.fuel_spent(fuel_current)

        if fuel_spent is not None:
            time = self.distance / v_effective
            return time.quantize(Decimal('0.001')), fuel_spent.quantize(Decimal('0.001'))
        return None, None

    def heuristic(self):
        heuristic = self.distance / self.plane.cruise_speed
        return heuristic.quantize(Decimal('0.001'))







class System:
    def __init__(self):
        self.start = None
        self.end = None
        self.cities = {}  # name -> City
        self.routes = {}  # name -> list[tuple]
        self.plane = Plane()

    def add_city(self, city: City):
        if city.name not in self.cities:
            self.cities[city.name] = city
            self.routes[city.name] = []

    def add_flight(self, from_city, to_city, wind_speed, wind_direction):
        self.add_city(from_city)
        self.add_city(to_city)
        flight = Flight(from_city, to_city, self.plane, wind_speed, wind_direction)
        self.routes[from_city.name].append((to_city.name, flight))
        flight_back = Flight(to_city, from_city, self.plane, wind_speed, wind_direction)
        self.routes[to_city.name].append((from_city.name, flight_back))

    def load_from_json(self, path):
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        file.close()
        self.start = data["start"]
        self.end = data["end"]
        for city in data["cities"]:
            city = City(city["name"], city["lat"], city["lon"], city["has_fuel"])
            self.add_city(city)
        for flight in data["flights"]:
            fro = self.cities[flight["from"]]
            to = self.cities[flight["to"]]
            self.add_flight(fro, to, flight["wind_speed"], flight["wind_direction"])
        print("Успешно загружено!")

    def a_star(self):
        queue = [(Decimal("0"), Decimal("0"), Decimal("0"), (self.start, self.plane.tank_capacity))]

        route = {}
        route[self.start] = (None, "", False)

        # ❌ ВАЖНО: distance по городу нельзя использовать как в Dijkstra
        # но мы оставим как "best time per state approximation"
        best = {}

        start_state = (self.start, self.plane.tank_capacity)
        best[start_state] = Decimal("0")

        distance_we_flew_global = Decimal("0")

        while queue:
            f, fuel_we_spent, distance_we_flew, state = heapq.heappop(queue)
            city = state[0]
            fuel_we_can_use = state[1]

            current_state = (city, fuel_we_can_use)

            # ❗ пропускаем устаревшие состояния
            if current_state in best and best[current_state] < distance_we_flew:
                continue

            if city == self.end:
                return self.reconstruct_path(route, self.end), distance_we_flew, fuel_we_spent, Decimal("0")

            for neighbor, flight in self.routes[city]:
                current_fuel = fuel_we_can_use

                time, fuel_spent = flight.time(current_fuel)
                city_obj = self.cities[city]

                did_refuel = False

                if not time and city_obj.has_fuel:
                    current_fuel = self.plane.tank_capacity
                    time, fuel_spent = flight.time(current_fuel)

                    if not time:
                        continue

                    time += city_obj.time_full_tank
                    did_refuel = True

                elif not time:
                    continue

                new_distance = distance_we_flew + time
                new_fuel_we_spent = fuel_we_spent + fuel_spent

                new_fuel_we_can_use = current_fuel - fuel_spent
                new_state = (neighbor, new_fuel_we_can_use)

                # ❗ ключевая фиксация: best по state, а не по city
                if new_state in best and best[new_state] <= new_distance:
                    continue

                best[new_state] = new_distance

                to_city = self.cities[self.end]
                h_flight = Flight(self.cities[neighbor], to_city, self.plane, 0, 0)
                new_h_distance = new_distance + h_flight.heuristic()

                flight_str = (f"{city} -> {neighbor} : {time.quantize(Decimal('0.01'))}"
                              f" ч, {flight.distance.quantize(Decimal('1'))} км, "
                              f"{fuel_spent.quantize(Decimal('1'))} л")

                route[neighbor] = (city, flight_str, did_refuel)

                heapq.heappush(queue, (
                    new_h_distance,
                    new_fuel_we_spent,
                    new_distance,
                    new_state
                ))

        return None, Decimal("inf"), Decimal("inf")

    def reconstruct_path(self, route, end):
        data = []
        current = end

        if end not in route and end != self.start:
            return [self.start]

        while current:
            prev_city, flight_str, did_refuel = route[current]
            if flight_str:
                data.append(flight_str)
            if did_refuel:
                data.append(f"[Дозаправка {current}: +0.5 ч]")

            current = prev_city
        data.reverse()
        return data

def to_json(path, path_list, total_time, total_fuel, total_distance):
    refuel_count = sum(1 for step in path_list if "Дозаправка" in step)
    output_data = {
            "start": system.start,
            "end": system.end,
            "path": path_list,
            "total_time": float(total_time.quantize(Decimal('0.01'))),
            "total_distance": int(total_distance.quantize(Decimal('1'))),
            "total_fuel_spent": int(total_fuel.quantize(Decimal('1'))),
            "refuels": refuel_count}

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    f.close()


system = System()
system.load_from_json("flights.json")
to_json("flying.json", *system.a_star())