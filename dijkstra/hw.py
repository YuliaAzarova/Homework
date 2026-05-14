import json, math, heapq

class Node:
    def __init__(self, id, scatter_coeff, sensor, threshold):
        self.id = id
        self.scatter_coeff = scatter_coeff
        self.sensor = sensor
        self.threshold = threshold


class Edge:
    def __init__(self, u, v, length_m, material, attenuation, noise_coeff, directed):
        self.u = u
        self.v = v
        self.length_m = length_m
        self.material = material
        self.attenuation = attenuation
        self.noise_coeff = noise_coeff
        self.directed = directed

    def travel_time_ms(self, material_speeds: dict[str, float]) -> float:
        t = self.length_m / material_speeds[self.material]
        return t * 1000

    def other(self, node):
        if self.u == node:
            return self.v
        if not self.directed and self.v == node:
            return self.u
        return None

    def propagate_energy(self, E_in: float) -> float:
        E_out = E_in * math.exp(-self.attenuation * self.length_m)
        return E_out

    def propagate_noise(self, noise_in: float) -> float:
        noise_out = noise_in + self.noise_coeff
        return noise_out

class SignalSystem:
    def __init__(self):
        self.start = None
        self.R_ms = 0
        self.initial_energy = 0
        self.alpha = 0
        self.beta = 0
        self.gamma = 0
        self.materials = {}
        self.nodes = {}
        self.graph = {}
        self.states = {}

    def add_node(self, id, scatter_coeff, sensor, threshold):
        if id not in self.nodes:
            self.nodes[id] = Node(id, scatter_coeff, sensor, threshold)
            self.graph[id] = []

    def add_edge(self, u, v, length_m, material, attenuation, noise_coeff, directed):
        edge = Edge(u, v, length_m, material, attenuation, noise_coeff, directed)
        self.graph[u].append(edge)

        if not directed:
            self.graph[v].append(Edge(v, u, length_m, material, attenuation, noise_coeff, directed))

    def load_from_json(self, path: str):
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        file.close()

        self.start = data["start"]
        self.R_ms = data["R_ms"]
        self.initial_energy = data["initial_energy"]
        self.alpha = data["alpha"]
        self.beta = data["beta"]
        self.gamma = data["gamma"]
        self.materials = data["materials"]

        for node in data["vertices"]:
            self.add_node(node["id"], node["scatter_coeff"], node["sensor"], node["threshold"])
        for edge in data["edges"]:
            self.add_edge(edge["u"], edge["v"], edge["length_m"],
                          edge["material"], edge["attenuation"],
                          edge["noise_coeff"], edge["directed"])
        print("Успешно загружено!")


    def dijkstra(self):
        heap = [
            (0.0, 0.0, self.start, self.initial_energy, 0.0, None)
        ]
        best = {}
        self.states = {}

        while heap:
            cost, time, node_id, energy, noise, parent = heapq.heappop(heap)
            if time > self.R_ms or energy <= 0:
                continue

            if node_id in best and cost > best[node_id]:
                continue

            best[node_id] = cost
            self.states[node_id] = {"time_ms": time, "energy": energy,
                "noise": noise, "cost": cost, "parent": parent}

            for edge in self.graph[node_id]:
                neighbor_id = edge.other(node_id)

                if not neighbor_id:
                    continue

                node = self.nodes[neighbor_id]
                new_time = time + edge.travel_time_ms(self.materials)
                E_after = edge.propagate_energy(energy)
                new_energy = E_after * (1 - node.scatter_coeff)
                new_noise = noise + edge.noise_coeff

                if new_time > self.R_ms or new_energy <= 0:
                    continue

                new_cost = (self.gamma * new_time
                            + self.alpha * new_noise
                            + self.beta * (1 / new_energy))

                heapq.heappush(heap,(new_cost, new_time, neighbor_id,
                                     new_energy, new_noise, node_id))

        return self.states


    def restore_path(self, node_id):
        path = []
        cur = node_id

        while cur is not None:
            path.append(cur)
            cur = self.states[cur]["parent"]

        return path[::-1]

    def to_json(self):
        sensors = {}

        for node_id, node in self.nodes.items():
            if not node.sensor:
                continue

            if node_id not in self.states:
                continue

            state = self.states[node_id]

            if state["time_ms"] <= self.R_ms and state["energy"] >= node.threshold:
                sensors[node_id] = {
                    "time_ms": round(state["time_ms"], 2),
                    "energy": round(state["energy"], 2),
                    "noise": round(state["noise"], 2),
                    "cost": round(state["cost"], 2),
                    "path": self.restore_path(node_id)
                }
        result = {"R_ms": self.R_ms,
            "reachable_sensors": sensors}

        with open("result.json", "w", encoding="utf-8") as file:
            json.dump(result, file, indent=4, ensure_ascii=False)

ss = SignalSystem()
ss.load_from_json("data.json")
ss.dijkstra()
ss.to_json()
