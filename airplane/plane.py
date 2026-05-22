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
        density_fuel = Decimal("0.8")
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
        self.wind_speed = Decimal(str(wind_speed))
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
        plane_speed = self.plane.get_speed(fuel_current)
        speed_multiplier = Decimal("1") + Decimal("0.05") * self.dir_diff
        effective = plane_speed * speed_multiplier
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
        time = self.distance / v_effective
        fuel_spent = self.fuel_spent(fuel_current)

        if fuel_spent is not None:
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
        start_state = (self.start, self.plane.tank_capacity)
        queue = [(Decimal("0"), Decimal("0"), Decimal("0"), start_state)]

        route = {}
        route[self.start] = (None, "", False)

        best_time = {point: Decimal("inf") for point in self.cities}
        best_time[self.start] = Decimal("0")

        while queue:
            f, fuel_spent, distance, state = heapq.heappop(queue)
            city, current_fuel = state[0], state[1]

            if city == self.end:
                return self.reconstruct_path(route, self.end), best_time[self.end], fuel_spent, distance

            for neighbor, flight in self.routes[city]:
                fuel_remaining = current_fuel
                time, flight_fuel_spent = flight.time(fuel_remaining)
                city_obj = self.cities[city]
                did_refuel = False

                if (not time or not flight_fuel_spent) and city_obj.has_fuel:
                    fuel_remaining = self.plane.tank_capacity
                    time, flight_fuel_spent = flight.time(fuel_remaining)

                    if not time or not flight_fuel_spent:
                        continue

                    time += city_obj.time_full_tank
                    did_refuel = True

                elif not time or not flight_fuel_spent:
                    continue

                if flight_fuel_spent > fuel_remaining:
                    if city_obj.has_fuel and not did_refuel:
                        fuel_remaining = self.plane.tank_capacity
                        time, flight_fuel_spent = flight.time_and_fuel(fuel_remaining)

                        if time is None or flight_fuel_spent is None:
                            continue
                        if flight_fuel_spent > fuel_remaining:
                            continue

                        time += Decimal("0.5")
                        did_refuel = True
                    else:
                        continue

                new_time = best_time[city] + time

                if new_time < best_time[neighbor]:
                    best_time[neighbor] = new_time

                    h_flight = Flight(self.cities[neighbor], self.cities[self.end], self.plane, 0, 0)
                    h_time = h_flight.distance/self.plane.cruise_speed
                    f_total = new_time + h_time

                    flight_str = f"{city} -> {neighbor} : {time.quantize(Decimal('0.01'))} ч, {flight.distance.quantize(Decimal('1'))} км, {flight_fuel_spent.quantize(Decimal('1'))} л"
                    route[neighbor] = (city, flight_str, did_refuel)

                    new_fuel_spent = fuel_spent + flight_fuel_spent
                    new_distance = distance + flight.distance
                    new_current_fuel = (fuel_remaining - flight_fuel_spent).quantize(Decimal("0.001"))

                    new_state = (neighbor, new_current_fuel)
                    heapq.heappush(queue, (f_total, new_fuel_spent, new_distance, new_state))

        return None, Decimal("inf"), Decimal("inf"), Decimal("inf")

    def reconstruct_path(self, route, end):
        if end not in route:
            return [self.start]

        path = []
        current = end

        while current and current in route:
            prev_city, flight_log, did_refuel = route[current]

            if flight_log:
                path.append(flight_log)
            if did_refuel:
                path.append(f"[Дозаправка {prev_city}: +0.5 ч]")

            current = prev_city

        path.reverse()
        return path

def to_json(path, routes, total_time, total_fuel, total_distance):
    refuel_count = sum(1 for step in routes if "Дозаправка" in step)
    output_data = {
            "start": system.start,
            "end": system.end,
            "path": routes,
            "total_time": float(total_time.quantize(Decimal('0.01'))),
            "total_distance": int(total_distance.quantize(Decimal('1'))),
            "total_fuel_spent": int(total_fuel.quantize(Decimal('1'))),
            "refuels": refuel_count}

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    f.close()
    print("Записано в файл")


system = System()
system.load_from_json("flights.json")
to_json("flying.json", *system.a_star())