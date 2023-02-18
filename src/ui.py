import tkinter as tk

from repositories import ProductRepository, CustomerRepository, OrderRepository
from engines import mysql_engine_factory, sqlite_engine_factory, postgres_engine_factory
from export import export_data, recreate_tables


class Window:
    _WINDOW_SIZE = "1000x640"
    _CUSTOMERS_COLUMNS = ("ID", "Fullname", "Email")
    _PRODUCTS_COLUMNS = ("ID", "Name", "Price", "Description")
    _ORDERS_COLUMNS = ("ID", "Qty", "UserId", "ProductId")

    def __init__(self) -> None:
        self._window = tk.Tk()

        self._mysql_engine = mysql_engine_factory()
        self._product_repository = ProductRepository(self._mysql_engine)
        self._customer_repository = CustomerRepository(self._mysql_engine)
        self._order_repository = OrderRepository(self._mysql_engine)

        self._sqlite_engine = sqlite_engine_factory()
        self._postgres_engine = postgres_engine_factory()

    def _init_window(self) -> None:
        self._window.geometry(self._WINDOW_SIZE)
        self._window.configure(bg="azure3")
        self._window.title("Illia-Vlad SHOP")

    def _export_from_mysql_to_postgres(self) -> None:
        export_data(self._mysql_engine, self._postgres_engine)

    def _export_from_postgres_to_sqlite(self) -> None:
        export_data(self._postgres_engine, self._sqlite_engine)

    def _recreate_mysql_tables(self) -> None:
        recreate_tables(self._mysql_engine)

    def run(self) -> None:
        self._window.mainloop()
