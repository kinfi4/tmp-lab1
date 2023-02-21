from src.ui import CustomersWindow
from src.export import recreate_tables


def _initialize_database():
    pass


if __name__ == "__main__":

    window = CustomersWindow()
    window.run()

    recreate_tables(window._mysql_engine)

    window._customer_repository.add({"id": 1, "full_name": "Nick", "email": "espozito@dog.com"})
    window._customer_repository.add({"id": 2, "full_name": "John", "email": "foaspi@dog.com"})

    window._product_repository.add({"id": 1, "name": "Ball", "price": 9.5, "description":"Ball for football"})
    window._product_repository.add({"id": 2, "name": "Hog", "price": 15, "description":"Hog for farming"})

    window._order_repository.add({"id": 1, "customer_id": 1, "product_id": 1, "qty": 1})
