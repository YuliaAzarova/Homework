from random import randint
class Node:
    def __init__(self, value: int, priority: int=None, left=None, right=None):
        self.value = value
        self.priority = priority if priority else randint(1, 100)
        self.left = left
        self.right = right

class Treap:
    def __init__(self):
        self.root = None

    def print(self):
        def _print(root, level):
            if root is None:
                return
            _print(root.right, level + 1)
            print("     " * level, "->", root.value, f"[{root.priority}]")
            _print(root.left, level + 1)
        _print(self.root, 0)

    def insert(self, new_value):
        def _insert(curr:Node):
            if not curr:
                return Node(new_value)
            if new_value < curr.value:
                curr.left = _insert(curr.left)
            else:
                curr.right = _insert(curr.right)
            return self.rotate(curr)

        if not self.root:
            self.root = Node(new_value)
        else:
            self.root = _insert(self.root)

    def delete(self, value):
        def _delete(curr:Node):
            if not curr:
                return None
            if curr.value == value:
                curr.priority = -1
            elif curr.value > value:
                curr.left = _delete(curr.left)
            elif curr.value < value:
                curr.right = _delete(curr.right)
            return self.rotate(curr)
        self.root = _delete(self.root)



    def rotate(self, node: Node):
        if node.left and node.left.priority > node.priority:
            return self.rightRotate(node)
        if node.right and node.right.priority > node.priority:
            return self.leftRotate(node)
        return node

    def leftRotate(self, node):
        right_child = node.right
        right_child_left = right_child.left
        right_child.left = node
        node.right = right_child_left
        return right_child

    def rightRotate(self, node):
        left_child = node.left
        left_child_right = left_child.right
        left_child.right = node
        node.left = left_child_right
        return left_child

treap = Treap()
treap.insert(1)
treap.insert(2)
treap.insert(3)
treap.insert(0)
treap.print()
treap.delete(1)
treap.print()