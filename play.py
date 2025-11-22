from abc import abstractmethod, ABC
from random import *
class Entity(ABC):
    def __init__ (self, position: tuple[int, int]):
        self.position = position
    
    @abstractmethod
    @staticmethod
    def symbol():
        pass
#готово
class Damageable(ABC): #готово
    def __init__(self, hp:float, max_hp):
        self.hp = hp
        self._max_hp = max_hp
    
    def is_alive(self): #готово
        if self.hp <= 0:
            return False
        return True
    
    def heal(self, amount): #готово
        self.hp += amount
        if self.hp > self._max_hp:
            self.hp = self._max_hp
        return amount
    
    def take_damage(self, amount): #готово
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
class Bonus(ABC, Entity):
    @abstractmethod
    def apply(self, player):
        pass
#готово

class Weapon(Entity):
    def __init__(self,position, name, max_damage):
        self.name = name
        self.max_damage = max_damage
        super().__init__(position)
    @abstractmethod
    def roll_damage(self):
        pass
    @abstractmethod
    def is_available(self):
        pass
    @staticmethod
    def symbol():
        return "W"
#готово
class MeleeWeapon(Weapon):
    def __init__(self, args):
        super().__init__(*args)
    @abstractmethod
    def damage(self, rage:float):
        return self.roll_damage()*rage
    @abstractmethod
    def is_available(self):
        pass
#готово
class RangedWeapon(Weapon):
    def __init__(self, args, ammo):
        self.ammo = ammo
        super().__init__(*args)
    def consume_ammo(self, n=1): #готово
        if n > self.ammo:
            return False
        self.ammo -= n
        return True

    @abstractmethod
    def is_available(self):
        pass
    
    def damage(self, accuracy):
        if self.consume_ammo():
            return self.roll_damage()*accuracy
        return self.roll_damage()
#готово

class Structure(ABC, Entity):
    @abstractmethod
    def interact(self, player:"Player"):
        pass
    @staticmethod
    def symbol():
        return "T"
#готово

class Enemy(ABC, Entity, Damageable, Attacker):
    def __init__(self, args, lvl, max_enemy_damage, reward_coins):
        self.lvl = lvl
        self.max_enemy_damage = max_enemy_damage
        self.reward_coins = reward_coins
        super().__init__(*args)
    
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
    def __init__(self, position, hp, max_hp, lvl, weapon:"Weapon", inventory:dict[str, int], rage, accuracy, statuses:dict[str, int]):
        super().__init__(position, hp, max_hp)
        self.lvl = lvl
        self.weapon = weapon
        self.inventory = inventory
        if rage >= 1.0:
            self.rage = rage
        else:
            self.rage = 1.0
        if accuracy >= 1.0:
            self.accuracy = accuracy
        else:
            self.accuracy = 1.0
        self.statuses = statuses
    
    def move(self, d_row, d_col):
        self.symbol(d_row, d_col)
    
    def attack(self, target: Damageable):
        pass
    def choose_weapon(self, new_weapon:"Weapon"):
        self.weapon = new_weapon
    def apply_status_tick(self):
        pass
    def add_coins(self, amount):
        self.inventory["coins"] += amount
    def use_bonus(self, bonus:"Bonus"):
        pass
    def buy_auto_if_needed(self, bonus_factory:callable[[str], "Bonus"]):
        pass
        

class Rat(Enemy):
    def __init__(self):
        self.infection_chance = 0.25
        self.flee_chance_low_hp = 0.10
        self.flee_thareshold = 0.15
        self.infection_damage_base = 5.0
        self.infection_turns = 200
    def before_turn(self, player:Player):
        pass
    def attack(self, target:Damageable):
        pass
class Spider(Enemy):
    def __init__(self, poison_chance=0.10, summon_chance_low_hp=0.10, poison_damage_base=15.0, 
                 poison_turns=2, reward_coins=250):
        super().__init__(reward_coins)
        self.poison_chance = poison_chance
        self.summon_chance_low_hp = summon_chance_low_hp
        self.poison_damage_base = poison_damage_base

    def before_turn(self, player:Player):
        pass
    def attack(self, target:Damageable):
        pass
class Skeleton(Enemy):
    def __init__(self, weapon:Weapon, reward_coins=150):
        self.weapon = weapon
        super().__init__(reward_coins)
    def before_turn(self, player):
        pass
    def attack(self, target: Damageable):
        pass
    def drop_loot(self, player:Player):
        if not isinstance(self.weapon, Fist):
            return self.weapon


class Fist(MeleeWeapon):
    def __init__(self, name, max_damage=20):
        self.name = name
        self.max_damage = max_damage
    def damage(self, rage):
        return super().damage(rage)
class Stick(MeleeWeapon):
    def __init__(self, name, max_damage, durability):
        self.name = name
        self.max_damage = max_damage
        self.durability = durability
    def is_available(self):
        return super().is_available()
    def damage(self, rage):
        self.durability -= 1
        return super().damage(rage)

class Bow(RangedWeapon):
    def  __init__(self, name, max_damage, ammo):
        super().__init__(name, max_damage, ammo)

    def is_available(self):
        return super().is_available()
    
    def damage(self, accuracy):
        self.ammo -= 1
        super().damage(accuracy)
class Revolver(RangedWeapon):
    def __init__(self, name, max_damage, ammo):
        super().__init__(name, ammo, max_damage)
    def is_available(self):
        return super().is_available()
    def damage(self, accuracy):
        return super().damage(accuracy)

class Medkit(Bonus):
    def __init__(self, power):
        self.power = power
    def apply(self, player:Player):
        pass
class Rage(Bonus):
    def __init__(self, multiplier):
        self.multiplier = multiplier
    def apply(self, player:Player):
        pass
class Arrows(Bonus):
    def __init__(self, amount):
        self.amount = amount
    def apply(self, player:Player):
        if isinstance(player.weapon, Bow):
            player.weapon.ammo += self.amount
        else:
            pass
class Bullets(Bonus):
    def __init__(self, amount):
        self.amount = amount
    def apply(self, player:Player):
        if isinstance(player.weapon, Revolver):
            player.weapon.ammo += self.amount
        else:
            pass
class Accuracy(Bonus):
    def __init__(self, multiplier):
        self.multiplier = multiplier
    def apply(self, player:Player):
        pass
class Coins(Bonus):
    def __init__(self, amount):
        self.amount = amount
    def apply(self, player:Player):
        player.inventory["coins"] += self.amount

class Tower(Structure):
    def __init__(self, reveal_radius=2):
        self.reveal_radius = reveal_radius
    def interact(self, board:"Board"):
        pass
class Board:
    def __init__(self, rows, cols, grid, start, goal):
        self.rows = rows
        self.cols = cols
        self.grid = grid
        self.start = start
        self.goal = goal

    def place(self, entity: Entity, pos: tuple[int, int]):
        pass
    def entity_at(self, pos: tuple[int, int]):
        pass
    def in_bounds(self, pos: tuple[int, int]):
        pass
    def render(self, player: Player):
        pass

def start(n: int, m: int, player_lvl: int) -> tuple[Board, Player]:
 pass

def game(board: Board, player: Player):
    pass

def main():
    pass