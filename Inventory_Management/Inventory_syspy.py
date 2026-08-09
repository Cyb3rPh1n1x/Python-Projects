"""
Object-Oriented Inventory Management System
--------------------------------------------
Single-file version combining:
  - Custom exceptions
  - Product class
  - Inventory class (JSON persistence + thread-safe transaction context manager)
  - ShoppingCart class
  - Demo / test run

Run:  python3 inventory_system.py
"""

import json
import os
import threading


# =========================================================================
# Custom Exceptions
# =========================================================================

class InventoryError(Exception):
    """Base class for all inventory-related exceptions."""
    pass


class ItemNotFoundError(InventoryError):
    """Raised when a requested product SKU/id does not exist in the inventory."""

    def __init__(self, sku):
        self.sku = sku
        super().__init__(f"Item with SKU '{sku}' was not found in inventory.")


class OutOfStockError(InventoryError):
    """Raised when a requested quantity exceeds available stock."""

    def __init__(self, sku, requested, available):
        self.sku = sku
        self.requested = requested
        self.available = available
        super().__init__(
            f"Cannot fulfill request for {requested} unit(s) of '{sku}'. "
            f"Only {available} unit(s) available."
        )


class InvalidQuantityError(InventoryError):
    """Raised when a quantity value is invalid (e.g. zero or negative)."""

    def __init__(self, quantity):
        self.quantity = quantity
        super().__init__(f"Invalid quantity: {quantity}. Quantity must be a positive integer.")


# =========================================================================
# Product
# =========================================================================

class Product:
    def __init__(self, sku, name, price, quantity):
        self.sku = sku
        self.name = name
        self.price = float(price)
        self.quantity = int(quantity)

    def to_dict(self):
        return {
            "sku": self.sku,
            "name": self.name,
            "price": self.price,
            "quantity": self.quantity,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            sku=data["sku"],
            name=data["name"],
            price=data["price"],
            quantity=data["quantity"],
        )

    def __repr__(self):
        return f"Product(sku={self.sku!r}, name={self.name!r}, price={self.price}, quantity={self.quantity})"


# =========================================================================
# Inventory + thread-safe transaction context manager
# =========================================================================

class InventoryTransaction:
    """
    Custom context manager used as:

        with inventory.transaction() as txn:
            txn.deduct(sku, qty)
            txn.deduct(sku2, qty2)

    - Acquires a threading.Lock on __enter__, guaranteeing that stock checks
      and deductions across the whole transaction are atomic with respect to
      other threads.
    - Takes a snapshot of quantities before making changes. If any exception
      occurs inside the `with` block, all changes are rolled back before the
      exception propagates.
    - If the block completes successfully, the updated inventory is persisted
      to the JSON file and the lock is released.
    """

    def __init__(self, inventory):
        self.inventory = inventory
        self._snapshot = None

    def __enter__(self):
        self.inventory._lock.acquire()
        self._snapshot = {
            sku: product.quantity for sku, product in self.inventory.products.items()
        }
        return self

    def deduct(self, sku, quantity):
        self.inventory._deduct_stock_unlocked(sku, quantity)

    def add(self, sku, quantity):
        self.inventory._add_stock_unlocked(sku, quantity)

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                for sku, qty in self._snapshot.items():
                    if sku in self.inventory.products:
                        self.inventory.products[sku].quantity = qty
                return False
            else:
                self.inventory.save_to_file()
                return False
        finally:
            self.inventory._lock.release()


class Inventory:
    def __init__(self, json_path="products.json"):
        self.json_path = json_path
        self.products = {}  # sku -> Product
        self._lock = threading.Lock()

    # ---------- Persistence ----------

    def load_from_file(self):
        if not os.path.exists(self.json_path):
            self.products = {}
            return
        with open(self.json_path, "r") as f:
            data = json.load(f)
        self.products = {item["sku"]: Product.from_dict(item) for item in data}

    def save_to_file(self):
        data = [product.to_dict() for product in self.products.values()]
        with open(self.json_path, "w") as f:
            json.dump(data, f, indent=2)

    # ---------- Queries ----------

    def get_product(self, sku):
        if sku not in self.products:
            raise ItemNotFoundError(sku)
        return self.products[sku]

    def check_stock(self, sku, quantity):
        if quantity <= 0:
            raise InvalidQuantityError(quantity)
        product = self.get_product(sku)
        if product.quantity < quantity:
            raise OutOfStockError(sku, quantity, product.quantity)
        return True

    # ---------- Internal (must be called while holding the lock) ----------

    def _deduct_stock_unlocked(self, sku, quantity):
        if quantity <= 0:
            raise InvalidQuantityError(quantity)
        product = self.get_product(sku)
        if product.quantity < quantity:
            raise OutOfStockError(sku, quantity, product.quantity)
        product.quantity -= quantity

    def _add_stock_unlocked(self, sku, quantity):
        if quantity <= 0:
            raise InvalidQuantityError(quantity)
        product = self.get_product(sku)
        product.quantity += quantity

    # ---------- Public thread-safe operations ----------

    def deduct_stock(self, sku, quantity):
        with self.transaction() as txn:
            txn.deduct(sku, quantity)

    def add_stock(self, sku, quantity):
        with self.transaction() as txn:
            txn.add(sku, quantity)

    def transaction(self):
        return InventoryTransaction(self)

    def add_product(self, product):
        self.products[product.sku] = product

    def __repr__(self):
        return f"Inventory({len(self.products)} products)"


# =========================================================================
# ShoppingCart
# =========================================================================

class ShoppingCart:
    def __init__(self, inventory):
        self.inventory = inventory
        self.items = {}  # sku -> quantity requested

    def add_item(self, sku, quantity):
        if quantity <= 0:
            raise InvalidQuantityError(quantity)

        product = self.inventory.get_product(sku)  # raises ItemNotFoundError
        existing = self.items.get(sku, 0)
        total_requested = existing + quantity

        if product.quantity < total_requested:
            raise OutOfStockError(sku, total_requested, product.quantity)

        self.items[sku] = total_requested

    def remove_item(self, sku, quantity=None):
        if sku not in self.items:
            raise ItemNotFoundError(sku)
        if quantity is None or quantity >= self.items[sku]:
            del self.items[sku]
        else:
            self.items[sku] -= quantity

    def total_price(self):
        total = 0.0
        for sku, qty in self.items.items():
            product = self.inventory.get_product(sku)
            total += product.price * qty
        return total

    def checkout(self):
        """
        Atomically deducts every item in the cart from inventory using the
        Inventory's transaction context manager. If ANY item fails, the whole
        checkout is rolled back and no partial deduction persists.
        """
        if not self.items:
            raise ValueError("Cannot checkout an empty cart.")

        with self.inventory.transaction() as txn:
            for sku, qty in self.items.items():
                txn.deduct(sku, qty)

        receipt = {
            "items": dict(self.items),
            "total": self.total_price(),
        }
        self.items = {}
        return receipt

    def __repr__(self):
        return f"ShoppingCart(items={self.items})"


# =========================================================================
# Demo / self-test
# =========================================================================

def _seed_products_file(path):
    """Create a fresh products.json if one doesn't already exist next to this script."""
    if os.path.exists(path):
        return
    seed = [
        {"sku": "SKU001", "name": "Wireless Mouse", "price": 19.99, "quantity": 10},
        {"sku": "SKU002", "name": "Mechanical Keyboard", "price": 79.99, "quantity": 5},
        {"sku": "SKU003", "name": "USB-C Hub", "price": 34.50, "quantity": 0},
        {"sku": "SKU004", "name": "Webcam 1080p", "price": 45.00, "quantity": 3},
    ]
    with open(path, "w") as f:
        json.dump(seed, f, indent=2)


def _section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def demo_basic_flow(json_path):
    _section("1. Load inventory from products.json")
    inv = Inventory(json_path)
    inv.load_from_file()
    for p in inv.products.values():
        print(" ", p)

    _section("2. Successful shopping cart checkout")
    cart = ShoppingCart(inv)
    cart.add_item("SKU001", 2)
    cart.add_item("SKU002", 1)
    print("Cart:", cart)
    print("Total price: $%.2f" % cart.total_price())
    receipt = cart.checkout()
    print("Receipt:", receipt)
    print("SKU001 stock now:", inv.get_product("SKU001").quantity)
    print("SKU002 stock now:", inv.get_product("SKU002").quantity)

    _section("3. Custom exceptions instead of plain strings")
    try:
        inv.get_product("SKU999")
    except ItemNotFoundError as e:
        print("Caught ItemNotFoundError:", e)

    try:
        cart.add_item("SKU003", 1)  # SKU003 has 0 stock
    except OutOfStockError as e:
        print("Caught OutOfStockError:", e)

    try:
        cart.add_item("SKU001", -5)
    except InvalidQuantityError as e:
        print("Caught InvalidQuantityError:", e)

    _section("4. Failed checkout rolls back atomically (no partial deduction)")
    cart2 = ShoppingCart(inv)
    cart2.items = {"SKU004": 2, "SKU002": 999}  # second item impossible
    before = {sku: p.quantity for sku, p in inv.products.items()}
    try:
        cart2.checkout()
    except OutOfStockError as e:
        print("Caught OutOfStockError during checkout:", e)
    after = {sku: p.quantity for sku, p in inv.products.items()}
    print("Stock unchanged after rollback:", before == after)

    _section("5. Verify persistence to products.json")
    inv2 = Inventory(json_path)
    inv2.load_from_file()
    for p in inv2.products.values():
        print(" ", p)


def demo_concurrency(json_path):
    _section("6. Thread-safety: concurrent buyers racing for limited stock")
    inv = Inventory(json_path)
    inv.load_from_file()
    inv.products["SKU002"].quantity = 5  # reset for a clean demo
    inv.save_to_file()

    results = []
    results_lock = threading.Lock()

    def buyer(buyer_id, qty):
        try:
            inv.deduct_stock("SKU002", qty)
            with results_lock:
                results.append((buyer_id, "SUCCESS"))
        except OutOfStockError as e:
            with results_lock:
                results.append((buyer_id, f"FAILED: {e}"))

    threads = [threading.Thread(target=buyer, args=(i, 1)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for buyer_id, outcome in sorted(results):
        print(f"  Buyer {buyer_id}: {outcome}")

    successes = sum(1 for _, o in results if o == "SUCCESS")
    print(f"\nSuccessful purchases: {successes} (expected 5)")
    print("Final SKU002 stock:", inv.get_product("SKU002").quantity, "(expected 0)")


if __name__ == "__main__":
    products_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "products.json")
    _seed_products_file(products_path)
    demo_basic_flow(products_path)
    demo_concurrency(products_path)