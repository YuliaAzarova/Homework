import json
class Position:
    def __init__(self, first_name:str, second_name:str, name:str,
                 parent, subordinates:list = []):
        self.id = self.generate_id(first_name, second_name, name)
        self.first_name = first_name
        self.second_name = second_name
        self.name = name
        self.parent = parent
        self.subordinates = subordinates

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
                 parent=None, subordinates:list=[]) -> str:
        def _add(current:Position, pers:Position) -> str:
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

        person = Position(first_name, second_name, name, parent, subordinates)
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
                    current.subordinates.remove(sub)
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
print(company.add_direction("Спортивные", "Лагеря", "Петр", "Сергеев"))
print(company.add_direction("Разработка", "Программирование"))
company.print()
print(company.close_direction("Разработка"))
print(company.fired("Олег", "Гуляйкин"))
person = company.root.subordinates[0]
print(company.add_person(person))
company.print()