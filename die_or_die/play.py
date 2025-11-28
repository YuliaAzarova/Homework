from abc import abstractmethod, ABC
from random import *
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
            print(self.roll_damage()*accuracy)
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
#готово

class Player(Entity, Damageable, Attacker):
    def __init__(self, position, lvl, weapon: Weapon,
                 inventory:dict[str, list[Bonus]], statuses:dict[str, int], fight:bool):
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
        for i in self.statuses:
            self.statuses[i] -= 1
            if self.statuses[i] == 0:
                del self.statuses[i]
            if i == "infection":
                self.hp -= 5 * (1 + self.lvl / 10)
            else:
                self.hp = 15 * (1 + self.lvl / 10)
            if self.hp <= 0:
                return False
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

class Rat(Enemy):
    def __init__(self, position, weapon: MeleeWeapon):
        lvl = randint(1, 10)
        hp = 100 * (1 + lvl / 10)
        self.infection_chance = 0.25
        self.flee_chance_low_hp = 0.10
        self.flee_threshold = 0.15
        self.infection_damage_base = 5.0
        self.infection_turns = 3
        self.weapon = weapon
        super().__init__(position, max_hp=hp, hp=hp, max_enemy_damage=15 * (1 + lvl / 10), reward_coins=200)
    def before_turn(self, player:Player):
        if self.hp < self.max_hp*self.flee_threshold and randint(1, int(self.flee_chance_low_hp*100)) == 1:
            print("крыса убежала")
            player.coins += self.reward_coins
            player.change_fight(0)
        if "infection" not in player.statuses and randint(1, int(self.infection_chance*4*4)) == 1:
            print("Заражение")
            player.statuses["infection"] = self.infection_turns
        elif "infection" in player.statuses:
            player.take_damage(self.infection_damage_base)
    def attack(self, target:Damageable):
        self.max_damage = 15 * (1 + self.lvl / 10)
        return target.take_damage(self.weapon.damage(1.0))
#готов
class Spider(Enemy):
    def __init__(self, position, weapon: MeleeWeapon):
        lvl = randint(1, 10)
        hp = 100 * (1 + lvl / 10)
        self.weapon = weapon
        self.poison_chance = 0.1
        self.summon_chance_low_hp = 0.1
        self.poison_damage_base = 15.0
        self.call_threshold = 0.15
        self.poison_turns = 2
        super().__init__(position, max_hp=hp, hp=hp, max_enemy_damage=20 * (1 + lvl / 10), reward_coins=250)
    def before_turn(self, player:Player):
        if self.hp < self.max_hp * 0.15 and randint(1, 10) == 10:
            print("паук призвал паука")
        if randint(1, 10) == 10 and "poison" not in player.statuses:
            player.statuses["poison"] = self.poison_turns
            player.take_damage(self.poison_damage_base)
            print("Отравление")
        elif "poison" in player.statuses:
            player.take_damage(self.poison_damage_base)
    def attack(self, target:Damageable):
        self.max_damage = 20 * (1 + self.lvl / 10)
        return target.take_damage(self.weapon.damage(1.0))
#готово
class Skeleton(Enemy):
    def __init__(self, position, weapon:Weapon):
        lvl = randint(1, 10)
        hp = 100 * (1 + lvl / 10)
        self.weapon = weapon
        super().__init__(position, hp=hp, max_hp=hp, max_enemy_damage=10 * (1 + lvl / 10), reward_coins=150)
    def before_turn(self, player):
        pass
    def attack(self, target: Damageable):
        return target.take_damage(self.weapon.damage(1.0))
    def drop_loot(self, player:Player):
        if not isinstance(self.weapon, Fist):
            player.choose_weapon(self.weapon)
#готово


class Fist(MeleeWeapon):
    def __init__(self, name):
        self.max_damage = 20
        self.name = name
    def damage(self, rage):
        return super().damage(rage)
    def is_available(self):
        return True
#готово
class Stick(MeleeWeapon, ABC):
    def __init__(self, position, name):
        self.durability = randint(10, 20)
        max_damage = 25
        super().__init__(position, name, max_damage)
    def is_available(self):
        if self.durability > 0:
            return True
        return False
    def damage(self, rage):
        self.durability -= 1
        return super().damage(rage)
#готово
class Bow(RangedWeapon):
    def  __init__(self, position, name):
        max_damage = 35
        ammo = randint(10, 15)
        super().__init__(position, name, max_damage, ammo)

    def is_available(self):
        super().is_available()

    def damage(self, accuracy):
        super().damage(accuracy)
#готово
class Revolver(RangedWeapon):
    def __init__(self, position, name):
        max_damage = 45
        ammo = randint(5, 15)
        super().__init__(position, name, max_damage, ammo)
    def is_available(self):
        super().is_available()
    def damage(self, accuracy):
        if self.consume_ammo(2):
            return self.roll_damage() * accuracy
        return 0
#готово


class Medkit(Bonus):
    def __init__(self, position):
        self.power = randint(10, 40)
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
#готово
class Rage(Bonus):
    def __init__(self, position):
        self.multiplier = randint(1, 10)/10
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
#готово
class Arrows(Bonus):
    def __init__(self, position):
        self.amount = randint(1, 20)
        self.position = position
    def apply(self, player:Player):
        if isinstance(player.weapon, Bow):
            player.weapon.consume_ammo(self.amount)
            if player.fight:
                player.inventory["Arrows"].pop()
            return None
        player.inventory["Arrows"].append(self)
        return None
#готово
class Bullets(Bonus):
    def __init__(self, position):
        self.amount = randint(1, 10)
        self.position = position
    def apply(self, player:Player):
        if isinstance(player.weapon, Revolver):
            player.weapon.consume_ammo(self.amount)
            if player.fight:
                player.inventory["Bullets"].pop()
            return None
        player.inventory["Bullets"].append(self)
        return None
#готово
class Accuracy(Bonus):
    def __init__(self, position):
        self.multiplier = randint(1, 10)/10
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
#готово
class Coins(Bonus):
    def __init__(self, position):
        self.amount = randint(50, 100)
        self.position = position
    def apply(self, player:Player):
        player.inventory["Coins"] += self.amount
#готово

class Board:
    def __init__(self, rows, cols, grid: list[list[tuple[Entity | None, bool]]], start, goal):
        self.rows = rows
        self.cols = cols
        self.grid = grid
        self.start = start
        self.goal = goal
    def in_bounds(self, pos: tuple[int, int]):
        if self.grid[pos[0]][pos[1]] and pos != self.start and pos != self.goal:
            return True
        return False
    def place(self, entity: Entity, pos: tuple[int, int]):
        if self.in_bounds(pos):
            self.grid[pos[0]][pos[1]][0] = entity
    def entity_at(self, pos: tuple[int, int]):
        return self.grid[pos[0]][pos[1]][0]
    def render(self, player: Player):
        field = ""
        for i in range(self.rows*2+1):
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
                    if self.entity_at(coord):
                        field += f"|{self.entity_at(coord).symbol()}"
                    else:
                        field += "| "
            field += "|\n"
        for i in range(self.rows*2+1):
            field += "-"
        return field

class Tower(Structure):
    def __init__(self, position):
        self.reveal_radius = 2
        self.position = position
    def interact(self, board: Board):
        pass


def start(n: int, m: int, player_lvl: int):
    grid = [[(Entity|None, bool) for _ in range(m)] for _ in range(n)]
    weapons = ["stick", "bow", "revolver"]
    bonuses = ["medkit", "rage", "arrows", "bullets", "accuracy", "coins"]
    enemies = ["rat", "spider", "skeleton"]
    t = ["tower" for _ in range(m*n//100)]
    w = ["weapon" for _ in range(m * n // 20)]
    b = ["bonuse" for _ in range(m * n // 3)]
    e = ["enemy" for _ in range(m * n // 7)]
    i = m*n - m*n//100 - m*n//20 - m*n//3 - m*n//7
    s = [None for _ in range(i)]
    f = [*t, *w, *b, *e, *s]
    shuffle(f)
    f[0] = f[-1] = None
    chetchik = 0
    print(f)
    for i in range(m):
        for j in range(n):
            if f[chetchik] == "tower":
                cret = Tower()
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
    board = Board(m, n, grid, (0, 0), (m-1, n-1))

    player = Player((0, 0), lvl=player_lvl, weapon=Fist("your's hand"),
                    inventory={"Medkit": [], "Rage": [], "Arrows": [], "Bullets": [], "Accuracy": [], "Coins": 0},
                    statuses={}, fight=False)
    return (board, player)
#готово
def game(board: Board, player: Player):
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
            print("\n\n\033[35mПоздравляем вы прошли игру, не сдохли и не умерли !!!!!!")
            break

        if board.in_bounds(new_coord):
            if isinstance(board.entity_at(new_coord), Enemy):
                enemy = board.entity_at(new_coord)
                player.change_fight(True)
                print(f"\033[31m---------- На вас напали! ----------")
                while enemy.is_alive():
                    enemy.before_turn(player)
                    print(f"{type(enemy).__name__}\033[0m: damage: {enemy.attack(player)}, hp: {enemy.hp}")
                    if player.hp <= 0:
                        over = True
                        break
                    print(f"Текущее hp: {player.hp}\nИмеющиеся бонусы:", end=" ")
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
                        player.weapon = Fist("your's hand")
                player.change_fight(False)
                if isinstance(enemy, Skeleton):
                    enemy.drop_loot(player)
                board.grid[new_coord[0]][new_coord[1]] = (None, True)

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
            board.grid[new_coord[0]][new_coord[1]] = (board.entity_at(new_coord), True)

        if over or player.apply_status_tick() == False:
            print("\n\n\033[36mПроигрыш! Вы сдохли или умерли!!")
            break
        print("\033[0m", board.render(player))
        print(f"Текущее hp: {player.hp}\nКол-во монет: {player.inventory["Coins"]}")
        step = input("Куда вы хотите пойти? (w/a/s/d/stop) ")

starting = tuple(start(5, 5, 1))
game(starting[0], starting[1])