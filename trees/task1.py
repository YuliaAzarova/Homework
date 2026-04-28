import json
class Position:
    def __init__(self, id:str, first_name:str, second_name:str, name:str,
                 parent, subordinates:list):
        self.id = id
        self.first_name = first_name
        self.second_name = second_name
        self.name = name
        self.parent = parent
        self.subordinates = subordinates


class Company:
    def __init__(self, root:Position):
        self.root = root

    def add_person(self, person:Position) -> str:
        def _add(current:Position, pers:Position) -> str:
            if pers.parent == current.name:
                if current.name not in pers.subordinates:
                    current.subordinates.append(pers)
                    return "successfully added"
                return "person already existed"
            for sub in current.subordinates:
                res = _add(sub, pers)
                if res != "":
                    return res
            return ""

        res = _add(self.root, person)
        if res != "":
            return res
        return "no such parent"

    def add_direction(self, name:str, parent:str, first_name:str = None, second_name:str = None):
        id = ""
        if second_name:
            d = second_name
            if len(d) <= 2:
                d += "00"
            id += d[:3]
        if first_name:
            d = first_name
            if len(d) <= 2:
                d += "00"
            id += d[:3]
        d = name
        if len(d) <= 2:
            d += "00"
        id += d[:3]

        person = Position(id, first_name, second_name, name, parent, [])
        return self.add_person(person)

def upload_from_json(path:str):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    head = Position(data[0]["id"], data[0]["first_name"], data[0]["second_name"], data[0]["name"], data[0]["parent"], [])
    company = Company(head)
    for pers in data[1:]:
        person = Position(pers["id"], pers["first_name"], pers["second_name"], pers["name"], pers["parent"], [])
        company.add_person(person)
    return company

company = upload_from_json("/Users/julia/PycharmProjects/Homework/trees/data.json")
company.add_direction("Английские", "Лагеря", "Петр", "Сергеев")