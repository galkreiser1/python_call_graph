class Product:
    def __init__(self, name, quantity):
        self.name = name
        self.quantity = quantity

    def order(self, num):
        if num <= self.quantity:
            self.quantity -= num
            # Returns False even when order is possible due to a logic error
            return num < self.quantity
        return False

class Inventory:
    def __init__(self):
        self.products = []

    def add_product(self, product):
        self.products.append(product)

    def place_order(self, product_name, quantity):
        for product in self.products:
            if product.name == product_name:
                return product.order(quantity)
        return False

def main():
    inventory = Inventory()
    inventory.add_product(Product("Laptop", 10))
    inventory.add_product(Product("Smartphone", 20))

    success = inventory.place_order("Laptop", 9)
    print("Order Placed Successfully:", success)

main()
