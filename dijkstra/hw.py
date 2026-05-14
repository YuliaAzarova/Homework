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

    def other(self, node: Node) -> Node:
        if node.id == self.u:
            return self.v
        return self.u


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
        if not u in self.nodes or not v in self.nodes:
            return
        self.graph[u].append(Edge(u, v, length_m, material, attenuation, noise_coeff, directed))

        if not directed:
            self.graph[v].append(Edge(v, u, length_m, material, attenuation, noise_coeff, directed))

    def load_from_json(self, path: str):
        with open(path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        json_file.close()
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
        states = {}
        for node_id in self.nodes:
            states[node_id] = {
                "time_ms": float("inf"), "energy": 0,
                "noise": float("inf"), "cost": float("inf"), "parent": None }
        states[self.start] = {
            "time_ms": 0, "energy": self.initial_energy,
            "noise": 0, "cost": 0, "parent": None }

        heap = [(0, self.start)]

        while heap:
            current_cost, current_id = heapq.heappop(heap)
            current_state = states[current_id]

            if current_cost > states[current_id]["cost"]:
                continue

            for edge in self.graph[current_id]:
                neighbor_id = edge.v
                neighbor_node = self.nodes[neighbor_id]

                new_time = current_state["time_ms"] + edge.travel_time_ms(self.materials)
                E_after = edge.propagate_energy(current_state["energy"])
                new_energy = E_after * (1 - neighbor_node.scatter_coeff)
                new_noise = edge.propagate_noise(current_state["noise"])

                if new_time > self.R_ms or new_energy <= 0:
                    continue

                new_cost = (self.gamma * new_time
                            + self.alpha * new_noise
                            + self.beta * (1 / new_energy))

                if new_cost < states[neighbor_id]["cost"]:
                    states[neighbor_id] = {
                        "time_ms": new_time, "energy": new_energy,
                        "noise": new_noise, "cost": new_cost, "parent": current_id }
                    heapq.heappush(heap, (new_cost, neighbor_id))

        self.states = states
        return states


    def restore_path(self, states, node_id):
        path = []
        current = node_id

        while current:
            path.append(current)
            current = states[current]["parent"]
        path.reverse()
        return path

    def to_json(self):

        sensors = {}

        for node_id, node in self.nodes.items():
            if not node.sensor:
                continue

            state = self.states[node_id]
            if (state["time_ms"] <= self.R_ms
                    and state["energy"] >= node.threshold and state["cost"] != float("inf")):
                sensors[node_id] = {
                    "time_ms": state["time_ms"],
                    "energy": state["energy"],
                    "noise": state["noise"],
                    "cost": state["cost"],
                    "path": self.restore_path(self.states, node_id)
                }
        data = {
            "R_ms": self.R_ms,
            "reachable_sensors": sensors
        }
        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

ss = SignalSystem()
ss.load_from_json("data.json")
ss.dijkstra()
ss.to_json()
