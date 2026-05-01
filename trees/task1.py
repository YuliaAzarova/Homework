import json
class Position:
    def __init__(self, first_name:str, second_name:str, name:str,
                 parent, subordinates:list = None):
        self.id = self.generate_id(first_name, second_name, name)
        self.first_name = first_name
        self.second_name = second_name
        self.name = name
        self.parent = parent
        self.subordinates = subordinates if subordinates else []

    @staticmethod
    def generate_id(first_name: str, second_name: str, name: str) -> str:
        id = ""
        id += (second_name + "000")[:3]
        id += (first_name + "000")[:3]
        id += (name + "000")[:3]
        return id


class Company:
    def __init__(self, root:Position):
        self.root = root

    def add_person(self, first_name:str="", second_name:str="", name:str="",
                 parent=None) -> str:
        def _add(current:Position, pers:Position) -> str:
            if pers.name == current.name:
                if not current.first_name and not current.second_name:
                    current.parent.subordinates[current.parent.subordinates.index(current)] = pers
                    return "successfully added"
                return "person already existed"
            if pers.parent == current.name:
                for sub in current.subordinates:
                    if pers.name == sub.name:
                        if not sub.first_name and not sub.second_name:
                            current.subordinates[current.subordinates.index(sub)] = pers
                            return "successfully added"
                        return "person already existed"
                current.subordinates.append(pers)
                return "successfully added"

            for sub in current.subordinates:
                res = _add(sub, pers)
                if res != "no such parent":
                    return res
            return "no such parent"

        person = Position(first_name, second_name, name, parent)
        return _add(self.root, person)

    def add_direction(self, name:str, parent:str, first_name:str = "", second_name:str = ""):
        return self.add_person(first_name, second_name, name, parent)

    def print(self):
        def _print(current:Position, d:str):
            to_print = d + current.name + " (" + current.first_name + " " + current.second_name + ")"
            print(to_print)
            for sub in current.subordinates:
                k = d + "- - "
                _print(sub, k)

        _print(self.root, "")

    def close_direction(self, name:str) -> str:
        def _delete(current:Position):
            for sub in current.subordinates:
                if sub.name == name:
                    del current.subordinates[current.subordinates.index(sub)]
                    return "successfully deleted"
                res = _delete(sub)
                if res == "successfully deleted":
                    return res
            return "no such direction"
        return _delete(self.root)

    def fired(self, first_name:str, second_name:str):
        def _delete(current:Position) -> str:
            for sub in current.subordinates:
                if sub.first_name == first_name and sub.second_name == second_name:
                    current.subordinates[current.subordinates.index(sub)] = Position("", "", sub.name, sub.parent, sub.subordinates)
                    return "successfully fired"

                res = _delete(sub)
                if res == "successfully fired":
                    return res
            return "no such employee"

        return _delete(self.root)

    def redirect(self, name:str, to:str):
        def _find(current:Position) -> str:
            for sub in current.subordinates:
                if sub.name == name:
                    current.subordinates += sub.subordinates
                    del current.subordinates[current.subordinates.index(sub)]
                    result = self.add_person(sub.first_name, sub.second_name, sub.name, to)
                    if result == "successfully added":
                        return "successfully redirected"
                    return result
                res = _find(sub)
                if res == "successfully redirected":
                    return res
            return "no such directory"


        return _find(self.root)

def upload_from_json(path:str):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    head = Position(data[0]["first_name"], data[0]["second_name"], data[0]["name"], data[0]["parent"])
    company = Company(head)
    for pers in data[1:]:
        company.add_person(pers["first_name"], pers["second_name"], pers["name"], pers["parent"])
    return company


company = upload_from_json("data.json")
company.print()
print(company.add_direction("Разработка", "Программирование"))
print(company.add_person("Лев", "Сергеев", "Спортивные", "Лагеря"))
company.print()
print(company.close_direction("Разработка"))
print(company.fired("Олег", "Гуляйкин"))
print(company.redirect("Информатика", "Лагеря"))
company.print()