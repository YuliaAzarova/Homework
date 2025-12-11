from abc import abstractmethod, ABC
import json
from random import *

CLASS_SERIALIZE = {}

def register_class(cls):
    CLASS_SERIALIZE[cls.__name__] = cls
    return cls
class Entity(ABC):
    def __init__ (self, position: tuple[int, int]):
        self.position = position
    @staticmethod
    @abstractmethod
    def symbol():
        pass
#готово

class Damageable(ABC):
    def __init__(self, hp:float, max_hp):
        self.hp = hp
        self.max_hp = max_hp

    def is_alive(self):
        if self.hp <= 0:
            return False
        return True

    def heal(self, amount):
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        return amount

    def take_damage(self, amount:float):
        if self.hp <= amount:
            amount = self.hp
            self.hp = 0
            return amount
        self.hp -= amount
        return amount
#готово

class Attacker(ABC):
    @abstractmethod
    def attack(self, target:Damageable):
        pass
#готова

class Bonus(Entity):
    def __init__(self, position: tuple[int, int], price):
        self.position = position
        self.price = price

    @abstractmethod
    def apply(self, player):
        pass

    @staticmethod
    def symbol():
        s = 'B'
        return s

    @abstractmethod
    def to_dict(self):
        pass
#готово

class Weapon(Entity):
    def __init__(self, position, name, max_damage):
        self.name = name
        self.max_damage = max_damage
        super().__init__(position)

    def roll_damage(self):
        return randint(1, self.max_damage)

    @abstractmethod
    def is_available(self):
        pass

    @abstractmethod
    def damage(self, detail):
        pass

    @staticmethod
    def symbol():
        return "W"

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    @abstractmethod
    def to_dict(self):
        pass
#готово

class MeleeWeapon(Weapon):
    def __init__(self, position, name, max_damage):
        super().__init__(position, name, max_damage)

    def damage(self, rage:float):
        return self.roll_damage()*rage

    @abstractmethod
    def is_available(self):
        pass
#готово

class RangedWeapon(Weapon):
    def __init__(self, position, name, max_damage, ammo):
        self.ammo = ammo
        super().__init__(position, name, max_damage)
    def consume_ammo(self, n=1):
        if n > self.ammo:
            return False
        self.ammo -= n
        return True

    @abstractmethod
    def is_available(self):
        if self.ammo > 0:
            return True
        return False

    def damage(self, accuracy):
        if self.consume_ammo():
            return self.roll_damage()*accuracy
        return 0.0
#готово


class Structure(Entity):
    @abstractmethod
    def interact(self, player:"Player"):
        pass

    @staticmethod
    def symbol():
        return "T"

    @classmethod
    def from_dict(cls, d):
        return cls(**d)
#готово


class Enemy(Entity, Damageable, Attacker):
    def __init__(self, position, max_hp, hp, max_enemy_damage, reward_coins):
        self.lvl = randint(1, 10)
        self.max_enemy_damage = max_enemy_damage
        self.reward_coins = reward_coins
        self.max_hp = max_hp
        self.hp = hp
        super().__init__(position)

    @abstractmethod
    def before_turn(self, player:"Player"):
        pass

    def roll_enemy_damage(self):
        damage = randint(1, self.max_enemy_damage)
        return damage

    @staticmethod
    def symbol():
        return "E"

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    @abstractmethod
    def to_dict(self):
        pass
#готово

@register_class
class Player(Entity, Damageable, Attacker):
    def __init__(self, position, lvl, weapon: Weapon,
                 inventory:dict[str, list[Bonus]], statuses:dict[str, int], fight:bool=False):
        super().__init__(position)
        self.hp = 150 * (1 + lvl / 10)
        self.max_hp = 150 * (1 + lvl / 10)
        self.lvl = lvl
        self.weapon = weapon
        self.inventory = inventory
        self.coins = 0
        self.rage = 1.0
        self.accuracy = 1.0
        self.statuses = statuses
        self.fight = fight

    def move(self, d_row, d_col):
        self.position = (d_row, d_col)

    def attack(self, target: Damageable):
        if isinstance(self.weapon, RangedWeapon):
            detail = self.accuracy
        else:
            detail = self.rage
        if not target.is_alive():
            self.change_fight(0)
        return target.take_damage(self.weapon.damage(detail))

    def choose_weapon(self, new_weapon:Weapon):
        choose = input("\033[0mВы хотите сменить оружие? (y/n) ")
        if choose == "y":
            self.weapon = new_weapon

    def apply_status_tick(self):
        to_del = []
        for i in self.statuses:
            self.statuses[i] -= 1
            if self.statuses[i] == 0:
                to_del.append(i)
            if i == "infection":
                damage = 5 * (1 + self.lvl / 10)
                print(f"\033[31mЗаражение: {damage}\033[0m")
            else:
                damage = 15 * (1 + self.lvl / 10)
                print(f"\033[31mОтравление: {damage}\033[0m")
            self.hp -= damage
            if self.hp <= 0:
                return False
        for i in to_del:
            del self.statuses[i]
        return True


    def add_coins(self, amount):
        self.inventory["Coins"] += amount

    def use_bonus(self, bonus: Bonus):
        if bonus:
            bonus.apply(self)

    def buy_auto_if_needed(self, bonus: Bonus):
        if self.inventory["Coins"] > bonus.price:
            self.inventory["Coins"] -= bonus.price
            self.inventory[type(bonus).__name__].append(bonus)
            self.use_bonus(bonus)
        else:
            print("У вас не хватает денег, чтобы купить этот бонус")

    @staticmethod
    def symbol():
        return "P"

    def change_fight(self, change):
        if self.fight != change:
            self.fight = not self.fight

    def to_dict(self):
        inv_to_d = {}
        for i in self.inventory:
            inv_to_d[i] = []
            if i == "Coins":
                inv_to_d[i].append(self.inventory[i])
            else:
                for j in range(len(self.inventory[i])):
                    inv_to_d[i].append(self.inventory[i][j].to_dict())
        return {
            "type": "Player",
            "attrs": {
                "position": self.position,
                "lvl": self.lvl,
                "weapon": self.weapon.to_dict(),
                "inventory": inv_to_d,
                "statuses": self.statuses,
            }
        }

    @classmethod
    def from_dict(cls, d):
        weapon = CLASS_SERIALIZE[d["attrs"]["weapon"]["type"]].from_dict(d["attrs"]["weapon"])
        inv_from_d = {}
        for i in d["attrs"]["inventory"]:
            inv_from_d[i] = []
            for j in d["attrs"]["inventory"][i]:
                if i == "Coins":
                    inv_from_d[i].append(j)
                else:
                    inv_from_d[i].append(CLASS_SERIALIZE[j["type"]].from_dict(j))
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), d["attrs"]["lvl"], weapon, inv_from_d, d["attrs"]["statuses"])
        return obj


@register_class
class Rat(Enemy):
    def __init__(self, position, weapon: MeleeWeapon, lvl=randint(1, 10)):
        hp = 100 * (1 + lvl / 10)
        self.infection_chance = 0.25
        self.flee_chance_low_hp = 0.10
        self.flee_threshold = 0.15
        self.infection_damage_base = 5.0
        self.infection_turns = 3
        self.weapon = weapon
        super().__init__(position, max_hp=hp, hp=hp, max_enemy_damage=15 * (1 + lvl / 10), reward_coins=200)

    def before_turn(self, player:Player):
        if "infection" not in player.statuses and randint(1, int(self.infection_chance*4*4)) == 1:
            print("\033[31mЗаражение\033[0m")
            player.statuses["infection"] = self.infection_turns
        elif "infection" in player.statuses:
            player.take_damage(self.infection_damage_base)
        if self.hp < self.max_hp*self.flee_threshold and randint(1, int(self.flee_chance_low_hp*100)) == 1:
            print("\033[31mкрыса убежала\033[0m")
            player.inventory["Coins"] += self.reward_coins
            player.change_fight(0)
            return True
        return False

    def attack(self, target:Damageable):
        self.max_damage = 15 * (1 + self.lvl / 10)
        return target.take_damage(self.weapon.damage(1.0))

    def to_dict(self):
        return {
            "type": "Rat",
            "attrs": {
                "position": self.position,
                "lvl": self.lvl,
                "weapon": self.weapon.to_dict()
            }
        }

    @classmethod
    def from_dict(cls, d):
        weapon = CLASS_SERIALIZE[d["attrs"]["weapon"]["type"]].from_dict(d["attrs"]["weapon"])
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), weapon, d["attrs"]["lvl"])
        return obj
#готов

@register_class
class Spider(Enemy):
    def __init__(self, position, weapon: MeleeWeapon, lvl=randint(1, 10)):
        hp = 100 * (1 + lvl / 10)
        self.weapon = weapon
        self.poison_chance = 0.1
        self.summon_chance_low_hp = 0.1
        self.poison_damage_base = 15.0
        self.call_threshold = 0.15
        self.poison_turns = 2
        super().__init__(position, max_hp=hp, hp=hp, max_enemy_damage=20 * (1 + lvl / 10), reward_coins=250)

    def before_turn(self, player:Player):
        if randint(1, 10) == 10 and "poison" not in player.statuses:
            player.statuses["poison"] = self.poison_turns
            player.take_damage(self.poison_damage_base)
            print("\033[31mОтравление\033[0m")
        elif "poison" in player.statuses:
            player.take_damage(self.poison_damage_base)
        if self.hp < self.max_hp * 0.15 and randint(1, 10) == 10:
            print("\033[31mпаук призвал паука\033[0m")
            return True
        return False

    def attack(self, target:Damageable):
        self.max_damage = 20 * (1 + self.lvl / 10)
        return target.take_damage(self.weapon.damage(1.0))

    def to_dict(self):
        return {
            "type": "Spider",
            "attrs": {
                "position": self.position,
                "lvl": self.lvl,
                "weapon": self.weapon.to_dict()
            }
        }

    @classmethod
    def from_dict(cls, d):
        weapon = CLASS_SERIALIZE[d["attrs"]["weapon"]["type"]].from_dict(d["attrs"]["weapon"])
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), weapon, d["attrs"]["lvl"])
        return obj
#готово

@register_class
class Skeleton(Enemy):
    def __init__(self, position, weapon:Weapon, lvl=randint(1, 10)):
        hp = 100 * (1 + lvl / 10)
        self.weapon = weapon
        super().__init__(position, hp=hp, max_hp=hp, max_enemy_damage=10 * (1 + lvl / 10), reward_coins=150)

    def before_turn(self, player):
        return False

    def attack(self, target: Damageable):
        return target.take_damage(self.weapon.damage(1.0))

    def drop_loot(self, player:Player):
        if not isinstance(self.weapon, Fist):
            player.choose_weapon(self.weapon)

    def to_dict(self):
        return {
            "type": "Skeleton",
            "attrs": {
                "position": self.position,
                "lvl": self.lvl,
                "weapon": self.weapon.to_dict()
            }
        }

    @classmethod
    def from_dict(cls, d):
        weapon = CLASS_SERIALIZE[d["attrs"]["weapon"]["type"]].from_dict(d["attrs"]["weapon"])
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), weapon, d["attrs"]["lvl"])
        return obj
#готово


@register_class
class Fist(MeleeWeapon):
    def __init__(self, name):
        super().__init__(position=(-1,-1), max_damage=20, name=name)

    def damage(self, rage):
        return super().damage(rage)

    def is_available(self):
        return True

    def to_dict(self):
        return {
            "type": "Fist",
            "attrs": {
                "name": self.name
            }
        }

    @classmethod
    def from_dict(cls, d):
        return cls(d["attrs"]["name"])
#готово

@register_class
class Stick(MeleeWeapon, ABC):
    def __init__(self, position, name, durability=randint(10, 20)):
        self.durability = durability
        max_damage = 25
        super().__init__(position, name, max_damage)

    def is_available(self):
        if self.durability > 0:
            return True
        return False

    def damage(self, rage):
        self.durability -= 1
        return super().damage(rage)

    def to_dict(self):
        return {
            "type": "Stick",
            "attrs": {
                "position": self.position,
                "name": self.name,
                "durability": self.durability
            }
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), d["attrs"]["name"], d["attrs"]["durability"])
        return obj
#готово

@register_class
class Bow(RangedWeapon):
    def  __init__(self, position, name, ammo=randint(10, 15)):
        max_damage = 35
        super().__init__(position, name, max_damage, ammo)

    def is_available(self):
        return super().is_available()

    def damage(self, accuracy):
        return super().damage(accuracy)

    def to_dict(self):
        return {
            "type": "Bow",
            "attrs": {
                "position": self.position,
                "name": self.name,
                "ammo": self.ammo
            }
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), d["attrs"]["name"], d["attrs"]["ammo"])
        return obj
#готово

@register_class
class Revolver(RangedWeapon):
    def __init__(self, position, name, ammo=randint(5, 15)):
        max_damage = 45
        super().__init__(position, name, max_damage, ammo)

    def is_available(self):
        return super().is_available()

    def damage(self, accuracy):
        if self.consume_ammo(2):
            return self.roll_damage() * accuracy
        return 0

    def to_dict(self):
        return {
            "type": "Revolver",
            "attrs": {
                "position": self.position,
                "name": self.name,
                "ammo": self.ammo
            }
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), d["attrs"]["name"], d["attrs"]["ammo"])
        return obj
#готово


@register_class
class Medkit(Bonus):
    def __init__(self, position, power=randint(10, 40)):
        self.power = power
        self.price = 75
        self.position = position

    def apply(self, player:Player):
        if player.fight:
            player.heal(self.power)
            player.inventory["Medkit"].pop()
            print("Использована аптечка")
            return None
        player.inventory["Medkit"].append(self)
        return None

    def to_dict(self):
        return {
            "type": "Medkit",
            "attrs": {
                "position": self.position,
                "power": self.power
            }
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), d["attrs"]["power"])
        return obj
#готово

@register_class
class Rage(Bonus):
    def __init__(self, position, multiplier=randint(1, 10)/10):
        self.multiplier = multiplier
        self.price = 50
        self.position = position

    def apply(self, player:Player):
        if player.fight:
            player.rage += self.multiplier
            player.inventory["Rage"].pop()
            print("Использована ярость")
            return None
        player.inventory["Rage"].append(self)
        return None

    def to_dict(self):
        return {
            "type": "Rage",
            "attrs": {
                "position": self.position,
                "multiplier": self.multiplier
            }
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), d["attrs"]["multiplier"])
        return obj
#готово

@register_class
class Arrows(Bonus):
    def __init__(self, position, amount=randint(1, 20)):
        self.amount = amount
        self.position = position

    def apply(self, player:Player):
        if isinstance(player.weapon, Bow):
            player.weapon.consume_ammo(self.amount)
            if player.fight:
                print("Добавлены стрелы")
                player.inventory["Arrows"].pop()
            return None
        player.inventory["Arrows"].append(self)
        return None

    def to_dict(self):
        return {
            "type": "Arrows",
            "attrs": {
                "position": self.position,
                "amount": self.amount
            }
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), d["attrs"]["amount"])
        return obj
#готово

@register_class
class Bullets(Bonus):
    def __init__(self, position, amount=randint(1, 10)):
        self.amount = amount
        self.position = position

    def apply(self, player:Player):
        if isinstance(player.weapon, Revolver):
            player.weapon.consume_ammo(self.amount)
            if player.fight:
                print("Добавлены пули")
                player.inventory["Bullets"].pop()
            return None
        player.inventory["Bullets"].append(self)
        return None

    def to_dict(self):
        return {
            "type": "Bullets",
            "attrs": {
                "position": self.position,
                "amount": self.amount
            }
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), d["attrs"]["amount"])
        return obj
#готово

@register_class
class Accuracy(Bonus):
    def __init__(self, position, multiplier=randint(1, 10)/10):
        self.multiplier = multiplier
        self.price = 50
        self.position = position

    def apply(self, player:Player):
        if player.fight:
            player.accuracy += self.multiplier
            player.inventory["Accuracy"].pop()
            print("Использована точность")
            return None
        player.inventory["Accuracy"].append(self)
        return None

    def to_dict(self):
        return {
            "type": "Accuracy",
            "attrs": {
                "position": self.position,
                "multiplier": self.multiplier
            }
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), d["attrs"]["multiplier"])
        return obj
#готово

@register_class
class Coins(Bonus):
    def __init__(self, position, amount=randint(50, 100)):
        self.amount = amount
        self.position = position

    def apply(self, player:Player):
        player.inventory["Coins"] += self.amount

    def to_dict(self):
        return {
            "type": "Coins",
            "attrs": {
                "position": self.position,
                "amount": self.amount
            }
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]), d["attrs"]["amount"])
        return obj
#готово


@register_class
class Board:
    def __init__(self, rows, cols, grid: list[list[tuple[Entity | None, bool]]]):
        self.rows = rows
        self.cols = cols
        self.grid = grid
        self.start = (0, 0)
        self.goal = (rows-1, cols-1)

    def in_bounds(self, pos: tuple[int, int]):
        if ((pos[0] < len(self.grid) and pos[1] < len(self.grid[0])) and
                pos != self.start and pos != self.goal and pos[0]>=0 and pos[1]>=0):
            return True
        return False

    def place(self, entity: Entity, pos: tuple[int, int]):
        if self.in_bounds(pos):
            self.grid[pos[0]][pos[1]] = (entity, False)

    def entity_at(self, pos: tuple[int, int]):
        return self.grid[pos[0]][pos[1]][0]

    def render(self, player: Player):
        field = ""
        for i in range(self.cols*2+1):
            field += "-"
        field += "\n"
        for i in range(self.rows):
            for j in range(self.cols):
                coord = (i, j)
                if coord == player.position:
                    field += f"|{player.symbol()}"
                    self.grid[coord[0]][coord[1]] = (self.grid[coord[0]][coord[1]][0], True)
                    continue
                if self.grid[i][j][1] == True:
                    if self.entity_at(coord):
                        field += f"|{self.entity_at(coord).symbol()}"
                    else:
                        field += "| "
                else:
                    field += "|X"
            field += "|\n"
        for i in range(self.cols*2+1):
            field += "-"
        return field

    def to_dict(self):
        grid_to_d = []
        for i in self.grid:
            row = []
            for j in i:
                if j is None:
                    row.append(None)
                elif isinstance(j, tuple):
                    if j[0] is None:
                        row.append([None, j[1]])
                    else:
                        row.append([j[0].to_dict(), j[1]])
                else:
                    row.append(j.to_dict())
            grid_to_d.append(row)
        return {
            "type": "Board",
            "attrs": {
                "rows": self.rows,
                "cols": self.cols,
                "grid": grid_to_d
            }
        }

    @classmethod
    def from_dict(cls, d):
        grid_from_d = []
        for i in d["attrs"]["grid"]:
            row = []
            for j in range(len(i)):
                if i[j][0] is None:
                    row.append((None, i[j][1]))
                else:
                    obj = CLASS_SERIALIZE[i[j][0]["type"]].from_dict(i[j][0])
                    row.append((obj, i[j][1]))
            grid_from_d.append(row)
        obj = cls(d["attrs"]["rows"], d["attrs"]["cols"], grid_from_d)
        return obj
# готово

@register_class
class Tower(Structure):
    def __init__(self, position):
        self.reveal_radius = 2
        self.position = position

    def interact(self, board: Board):
        print("interact")
        for i in range(self.position[1] - self.reveal_radius, self.position[1] + self.reveal_radius+1):
            for j in range(self.position[0] - self.reveal_radius, self.position[0] + self.reveal_radius+1):
                if board.in_bounds((i, j)):
                    board.grid[i][j] = (board.entity_at((i, j)), True)
        print(self.position[1] + 1 - self.reveal_radius, "  ", )

    def to_dict(self):
        return {
            "type": "Tower",
            "attrs": {
                "position": self.position,
            }
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls((d["attrs"]["position"][0], d["attrs"]["position"][1]))
        return obj
# готово

CLASS_SERIALIZE = {
    "Rat": Rat,
    "Spider": Spider,
    "Skeleton": Skeleton,
    "Fist": Fist,
    "Stick": Stick,
    "Bow": Bow,
    "Revolver": Revolver,
    "Medkit": Medkit,
    "Rage": Rage,
    "Arrows": Arrows,
    "Bullets": Bullets,
    "Accuracy": Accuracy,
    "Coins": Coins,
    "Tower": Tower
}

def start(player_lvl: int):
    lvl = input("Какой уровень сложности хотите выбрать? (easy/normal/hard) ")
    with open("difficulty.json", "r", encoding="utf-8") as file:
        difficulty = json.load(file)

    n = randint(difficulty[lvl]["board_min"], difficulty[lvl]["board_max"])
    m = randint(difficulty[lvl]["board_min"], difficulty[lvl]["board_max"])

    grid = [[(Entity|None, bool) for _ in range(m)] for _ in range(n)]

    weapons = ["stick", "bow", "revolver"]
    bonuses = ["medkit", "rage", "arrows", "bullets", "accuracy", "coins"]
    enemies = ["rat", "spider", "skeleton"]

    am_t = int(m * n * difficulty[lvl]["tower_multiplier"])
    am_w = int(m * n * difficulty[lvl]["weapon_multiplier"])
    am_b = int(m * n * difficulty[lvl]["bonus_multiplier"])
    am_e = int(m * n * difficulty[lvl]["enemy_multiplier"])

    t = ["tower" for _ in range(am_t)]
    w = ["weapon" for _ in range(am_w)]
    b = ["bonuse" for _ in range(am_b)]
    e = ["enemy" for _ in range(am_e)]
    i = m*n - am_t - am_w - am_b - am_e

    s = [None for _ in range(i)]
    f = [*t, *w, *b, *e, *s]
    shuffle(f)
    f[0] = f[-1] = None
    chetchik = 0

    for i in range(n):
        for j in range(m):

            if f[chetchik] == "tower":
                cret = Tower((i, j))

            elif f[chetchik] == "weapon":
                weapon = weapons[randint(0, 2)]
                if weapon == "stick":
                    cret = Stick((i, j), "stick")
                elif weapon == "bow":
                    cret = Bow((i, j), "bow")
                else:
                    cret = Revolver((i, j), "revolver")

            elif f[chetchik] == "bonuse":
                bonuse = bonuses[randint(0, 5)]
                if bonuse == "medkit":
                    cret = Medkit((i, j))
                elif bonuse == "rage":
                    cret = Rage((i, j))
                elif bonuse == "arrows":
                    cret = Arrows((i, j))
                elif bonuse == "bullets":
                    cret = Bullets((i, j))
                elif bonuse == "accuracy":
                    cret = Accuracy((i, j))
                else:
                    cret = Coins((i, j))

            elif f[chetchik] == "enemy":
                enemy = enemies[randint(0, 2)]
                if enemy == "rat":
                    cret = Rat((i, j), Fist("rat's hand"))
                elif enemy == "spider":
                    cret = Spider((i, j), Fist("spider's hand"))
                else:
                    cret = Skeleton((i, j), Fist("skeleton's hand"))

            else:
                cret = None

            grid[i][j] = (cret, False)

            chetchik += 1
    board = Board(n, m, grid)

    player = Player((0, 0), lvl=player_lvl, weapon=Fist("your's hand"),
                    inventory={"Medkit": [], "Rage": [], "Arrows": [], "Bullets": [], "Accuracy": [], "Coins": 0},
                    statuses={}, fight=False)
    return (board, player, lvl)
#готово

def save(player: Player, difficulty, lvl, board: Board, lvl_finished:bool):
    to_save = {"difficulty": difficulty, "current_level": lvl,
               "player": player.to_dict()}
    if lvl_finished:
        to_save["board"] = False
    else:
        to_save["board"] = board.to_dict()
    with open("save.json", "w") as f:
        json.dump(to_save, f, indent=4)
        print("\033[35mуспешное сохранение\033[0m")

def load():
    with open("save.json", "r", encoding="utf-8") as file:
        d = dict(json.load(file))
        difficulty = d["difficulty"]
        lvl = d["current_level"]
        player = Player.from_dict(d["player"])
        if d["board"] == False:
            board = None
        else:
            board = Board.from_dict(d["board"])
        return board, player, difficulty, lvl


def game(board: Board, player: Player, difficulty:str, lvl:int):
    print(board.render(player))
    print(f"Текущее hp: {player.hp}")
    step = input("Куда вы хотите пойти? (w/a/s/d/exit) ")
    while step != "exit":
        over = None
        if step == "w":
            new_coord = (player.position[0]-1, player.position[1])
        elif step == "a":
            new_coord = (player.position[0], player.position[1]-1)
        elif step == "s":
            new_coord = (player.position[0]+1, player.position[1])
        elif step == "d":
            new_coord = (player.position[0], player.position[1]+1)
        else:
            new_coord = (player.position[0], player.position[1])
        player.move(new_coord[0], new_coord[1])

        if player.position == board.goal:
            print("\n\n\033[35mПоздравляем вы прошли уровень, не сдохли и не умерли !!!!!!\033[0m")
            lvl += 1
            save(player, difficulty, lvl, board, lvl_finished=True)
            starting = tuple(start(player.lvl))
            board = starting[0]
            player.position = (0, 0)


        if board.in_bounds(new_coord):
            if isinstance(board.entity_at(new_coord), Enemy):
                player.change_fight(True)
                print(f"\033[31m---------- На вас напали! ----------")
                enemies = [board.entity_at(new_coord)]
                while len(enemies) != 0:
                    enemy = enemies[0]
                    if enemy.before_turn(player):
                        if isinstance(enemy, Spider):
                            enemies.append(Spider(new_coord, Fist("spider's hand")))
                        elif isinstance(enemy, Rat):
                            break
                    print(f"\033[31m{type(enemy).__name__}\033[0m: damage: {enemy.attack(player)}, hp: {enemy.hp}")
                    if player.hp <= 0:
                        over = True
                        break
                    print(f"Текущее hp: {player.hp}, оружие: {type(player.weapon).__name__}\nИмеющиеся бонусы:", end=" ")
                    for i in player.inventory:
                        if i != "Coins":
                                if len(player.inventory[i]) != 0:
                                    print(f"{i}: {len(player.inventory[i])}", end=", ")

                    print("Текущее кол-во монет:", player.inventory["Coins"])
                    bonus = input("Какой бонус хотите испльзовать? ")
                    if bonus in player.inventory and len(player.inventory[bonus]) != 0:
                        if (bonus == "Medkit" or (type(player.weapon).__name__ == "Revolver" and (bonus == "Bullets" or bonus == "Accuracy"))
                                or (type(player.weapon).__name__ == "Bow" and (bonus == "Arrows" or bonus == "Accuracy"))
                                or ((type(player.weapon).__name__ == "Stick" or type(player.weapon).__name__ == "Fist") and bonus == "Rage")):
                            player.use_bonus(player.inventory[bonus][0])
                        else:
                            print("Невозможно использовать бонус")
                    elif bonus in player.inventory and len(player.inventory[bonus]) == 0:
                        if bonus == "Medkit":
                            player.buy_auto_if_needed(Medkit(new_coord))
                        elif bonus == "Rage":
                            player.buy_auto_if_needed(Rage(new_coord))
                        elif bonus == "Accuracy":
                            player.buy_auto_if_needed(Accuracy(new_coord))
                        else:
                            print("Вы не можете купить этот бонус")
                    else:
                        print("Нет такого бонуса")

                    player.attack(enemy)
                    print("\nВы атаковали")
                    if not player.weapon.is_available():
                        if isinstance(player.weapon, RangedWeapon):
                            if len(player.inventory["Arrows"]) != 0 and type(player.weapon).__name__=="Bow":
                                player.inventory["Arrows"][0].apply(player)
                                print("Пополнен запас боеприпасов")
                            elif len(player.inventory["Bullets"]) != 0 and type(player.weapon).__name__=="Revolver":
                                player.inventory["Bullets"][0].apply(player)
                                print("Пополнен запас боеприпасов")
                            else:
                                player.weapon = Fist("your's hand")
                                print("Оружие недействительно")
                        else:
                            player.weapon = Fist("your's hand")
                            print("Оружие недействительно")
                    if not enemies[0].is_alive():
                        del enemies[0]
                        player.add_coins(enemy.reward_coins)
                        print("\033[31mВраг побежден\033[0m")

                player.change_fight(False)
                player.hp = Player(player.position, player.lvl+1, player.weapon,
                                player.inventory, player.statuses, player.fight).hp-player.hp
                if isinstance(enemy, Skeleton):
                    enemy.drop_loot(player)

                board.grid[new_coord[0]][new_coord[1]] = (None, True)
# готово
            elif isinstance(board.entity_at(new_coord), Weapon):
                print(f"\033[32m-----------Вы нашли оружие! -----------\n{type(board.entity_at(new_coord)).__name__}")
                old_w = player.weapon
                player.choose_weapon(board.entity_at(new_coord))
                if old_w != player.weapon:
                    if isinstance(old_w, Fist):
                        board.grid[new_coord[0]][new_coord[1]] = (None, True)
                    else:
                        board.place(old_w, new_coord)
# готово
            elif isinstance(board.entity_at(new_coord), Bonus):
                print(f"\033[32m-----------Вы получили бонус! -----------\n{type(board.entity_at(new_coord)).__name__}")
                board.entity_at(new_coord).apply(player)
                board.grid[new_coord[0]][new_coord[1]] = (None, True)
# готово
            elif isinstance(board.entity_at(new_coord), Tower):
                print(f"\033[33m-----------Вы открыли башню! -----------\033[0m\n")
                board.entity_at(new_coord).interact(board)
# готово

            board.grid[new_coord[0]][new_coord[1]] = (board.entity_at(new_coord), True)
            if over or player.apply_status_tick() == False:
                print("\n\n\033[36mПроигрыш! Вы сдохли или умерли!!")
                with open("records.json", "r", encoding="utf-8") as file:
                    records = dict(json.load(file))
                    new_records = {}
                if records["max_lvl"] < lvl:
                    new_records["max_lvl"] = lvl
                    new_records["coins"] = player.inventory["Coins"]
                elif records["max_lvl"] == lvl:
                    new_records["max_lvl"] = records["max_lvl"]
                    if records["coins"] < player.inventory["Coins"]:
                        new_records["coins"] = player.inventory["Coins"]
                    else:
                        new_records["coins"] = records["coins"]
                else:
                    new_records["max_lvl"] = records["max_lvl"]
                    new_records["coins"] = records["coins"]
                with open("records.json", "w", encoding="utf-8") as file:
                    file.write(json.dumps(new_records, indent=4))
                with open("save.json", "w", encoding="utf-8") as file:
                    file.write("")
                break
        else:
            print("За пределами поля!")



        print("\033[0m", board.render(player))
        print(f"lvl уровня: {lvl}\nТекущее hp: {player.hp}, lvl игрока: {player.lvl}\nКол-во монет: {player.inventory["Coins"]}")
        step = input("Куда вы хотите пойти? (w/a/s/d/exit) ")
        if step == "exit":
            save(player, difficulty, lvl, board, lvl_finished=False)

with open("save.json", "r", encoding="utf-8") as file:
    d = file.read()
if d == "":
    starting = tuple(start(1))
    game(starting[0], starting[1], starting[2], lvl=1)
else:
    board, player, difficulty, lvl = load()
    game(board, player, difficulty, lvl)