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

    def add_person(self, person:Position) -> bool:
        def _add(current:Position, pers:Position) -> bool:
            if pers.parent == current.name:
                current.subordinates.append(pers)
                return True
            for sub in current.subordinates:
                if _add(sub, pers):
                    return True
            return False

        if _add(self.root, person):
            return True
        return False

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