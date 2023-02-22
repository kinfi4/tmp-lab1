from typing import Any

import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Treeview

from src.exceptions import InfrastructureException, InvalidDataError, RelationError
from src.repositories import ProductRepository, CustomerRepository, OrderRepository
from src.engines import (
    mysql_engine_factory,
    sqlite_engine_factory,
    postgres_engine_factory,
)
from src.export import export_data
from src.constants import *


def is_float(value: Any) -> bool:
    """check whether it's float but also not throw error when it's string"""
    try:
        return isinstance(float(value), float)
    except ValueError:
        return False


def is_integer(value: Any) -> bool:
    """check whether it can be an int but also not throw error when it's string"""
    try:
        return isinstance(int(value), int)
    except ValueError:
        return False


class Window:
    def __init__(self) -> None:
        self._window = tk.Tk()

        self._window.geometry(WINDOW_SIZE)
        self._window.configure(bg="azure3")
        self._window.title("Illia-Vlad SHOP")
        self._window.resizable(False, False)

    def run(self) -> None:
        application = CustomersWindow()
        application.initialize_menu()

        self._window.mainloop()


class CustomersWindow:
    def __init__(self) -> None:
        self._mysql_engine = mysql_engine_factory()

        self._product_repository = ProductRepository(self._mysql_engine)
        self._customer_repository = CustomerRepository(self._mysql_engine)
        self._order_repository = OrderRepository(self._mysql_engine)

        self._sqlite_engine = sqlite_engine_factory()
        self._postgres_engine = postgres_engine_factory()

        self.frame = tk.Frame(bg=BACKGROUND)
        self.frame.pack()

        self.entry_frame = tk.Frame(bg=BACKGROUND)
        self.entry_frame.pack()

        self.listbox_frame = tk.Frame(bg=BACKGROUND)
        self.listbox_frame.pack()

        self.error_label = tk.Label()

        self.customers_tree = None
        self.id_entry = None
        self.email_entry = None
        self.full_name_entry = None

    def initialize_menu(self):
        self.frame.destroy()
        self.frame = tk.Frame(bg=BACKGROUND)
        self.frame.pack()

        self.entry_frame.destroy()
        self.entry_frame = tk.Frame(bg=BACKGROUND)
        self.entry_frame.pack()

        self.listbox_frame.destroy()
        self.listbox_frame = tk.Frame(bg=BACKGROUND)
        self.listbox_frame.pack()

        if self.error_label:
            self.error_label.destroy()

        # Create Main Buttons To Chose Which Table You Want To Add
        customer_button = tk.Button(
            self.frame,
            text="Customer",
            command=self.initialize_menu,
            width=30,
            bg=FOREGROUND,
        )
        customer_button.grid(row=0, column=0, pady=10)
        order_button = tk.Button(
            self.frame,
            text="Order",
            command=self.go_to_order_window,
            width=30,
            bg=FOREGROUND,
        )
        order_button.grid(
            row=0,
            column=1,
        )
        product_button = tk.Button(
            self.frame,
            text="Product",
            command=self.go_to_product_window,
            width=30,
            bg=FOREGROUND,
        )
        product_button.grid(row=0, column=2)
        export_postgres_button = tk.Button(
            self.frame,
            text="Export to Postgres",
            command=self._export_from_mysql_to_postgres,
            width=30,
            bg=FOREGROUND,
        )
        export_postgres_button.grid(row=1, column=3)

        export_sqlite_button = tk.Button(
            self.frame,
            text="Export from Postgres to Sqlite",
            command=self._export_from_postgres_to_sqlite,
            width=30,
            bg=FOREGROUND,
        )
        export_sqlite_button.grid(row=2, column=3)

        # Create text box labels for Customers
        id_label = tk.Label(self.entry_frame, text="ID:", bg=BACKGROUND)
        id_label.grid(row=1, column=0, sticky=tk.E)
        name_label = tk.Label(self.entry_frame, text="Customer name:", bg=BACKGROUND)
        name_label.grid(row=2, column=0, sticky=tk.E)
        email_label = tk.Label(self.entry_frame, text="Email:", bg=BACKGROUND)
        email_label.grid(row=3, column=0, sticky=tk.E)

        # Create Entry box for Customers
        self.id_entry = tk.Entry(self.entry_frame, width=30, bg=FOREGROUND)
        self.id_entry.grid(row=1, column=1)
        self.full_name_entry = tk.Entry(self.entry_frame, width=30, bg=FOREGROUND)
        self.full_name_entry.grid(row=2, column=1)
        self.email_entry = tk.Entry(self.entry_frame, width=30, bg=FOREGROUND)
        self.email_entry.grid(row=3, column=1)

        # clear, delete, update, exit buttons
        add_button = tk.Button(
            self.entry_frame,
            text="Add",
            command=self.add_customer,
            width=20,
            bg=FOREGROUND,
        )
        add_button.grid(row=0, column=2, padx=20)
        update_button = tk.Button(
            self.entry_frame,
            text="Update",
            command=self.update_customer,
            width=20,
            bg=FOREGROUND,
        )
        update_button.grid(row=2, column=2)
        clear_button = tk.Button(
            self.entry_frame,
            text="Clear",
            command=self.clear_customer_entries,
            width=20,
            bg=FOREGROUND,
        )
        clear_button.grid(row=3, column=2)
        delete_button = tk.Button(
            self.entry_frame,
            text="Delete",
            command=self.delete_customer,
            width=20,
            bg=FOREGROUND,
        )
        delete_button.grid(row=4, column=2)

        # creating listbox for customers
        self.listbox_frame = tk.Frame(bg=BACKGROUND)
        self.listbox_frame.pack()

        list_label = tk.Label(
            self.listbox_frame, text="list of customers", width=100, bg=BACKGROUND
        )
        list_label.grid(row=0, column=0)

        # creating treeview
        self.customers_tree = Treeview(
            self.listbox_frame, columns=CUSTOMER_COLUMN_FULL, show="headings", height=10
        )
        self.customers_tree.grid(row=1, column=0)

        for column_name, width in zip(CUSTOMER_COLUMN_FULL, CUSTOMER_COLUMN_FULL_SIZE):
            self.customers_tree.column(column_name, width=width, anchor=tk.CENTER)
            self.customers_tree.heading(column_name, text=column_name)

        scrollbar = tk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL)
        scrollbar.configure(command=self.customers_tree.set)
        self.customers_tree.configure(yscrollcommand=scrollbar)
        self.customers_tree.bind("<ButtonRelease-1>", self.get_selected_customer)

        # adding records from DB to list
        records = self._customer_repository.get_all()

        for i, item in enumerate(records):
            self.customers_tree.insert(
                "",
                index="end",
                iid=i,
                values=tuple(item[column] for column in CUSTOMER_COLUMN_FULL),
            )

    def _validate_input(self):
        if not self.full_name_entry.get():
            self.error_message("Can not update empty name.")
            return False
        if not self.email_entry.get() or not EMAIL_REGEX.match(self.email_entry.get()):
            self.error_message("'email' field is missing or have invalid format")
            return False

        return True

    def add_customer(self):
        """Adds new product, if all required entries are filled properly."""
        if self.error_label:
            self.error_label.destroy()

        validation_result = self._validate_input()
        if not validation_result:
            return

        try:
            self._customer_repository.add(
                {
                    "full_name": self.full_name_entry.get(),
                    "email": self.email_entry.get(),
                }
            )
        except InfrastructureException:
            self.error_message(
                "Something went wrong during customer adding, in case if error persist please contact support.")
            return
        else:
            self.initialize_menu()

    def update_customer(self):
        """Updates customer, if all required entries are filled properly."""
        if self.error_label:
            self.error_label.destroy()

        if not self.customers_tree.selection():
            self.error_message("please select one from listbox.")
            return

        validation_result = self._validate_input()
        if not validation_result:
            return

        self._customer_repository.update(
            self.id_entry.get(),
            {
                "full_name": self.full_name_entry.get(),
                "email": self.email_entry.get(),
            },
        )

        self.initialize_menu()

    def error_message(self, name):
        if self.error_label:
            self.error_label.destroy()

        self.error_label = tk.Label(
            self.entry_frame, text=name, bg=BACKGROUND, fg=ERROR_COLOR
        )
        self.error_label.grid(row=6, column=1)

    def delete_customer(self):
        if self.error_label:
            self.error_label.destroy()

        if not self.customers_tree.selection():
            self.error_message("please select one from listbox.")
            return

        selected_record = self.customers_tree.set(self.customers_tree.selection())

        answer = messagebox.askquestion("Are you sure?")
        if answer == "yes":
            self._customer_repository.delete(selected_record[CUSTOMER_COLUMN_FULL[0]])
            self.initialize_menu()
        else:
            self.error_message("record not exists in database.")

    def clear_customer_entries(self):
        """Clears all entries."""
        if self.error_label:
            self.error_label.destroy()

        self.id_entry.delete(0, tk.END)
        self.full_name_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)

    def get_selected_customer(self, event):
        """Inserts selected customer data into entries."""
        self.clear_customer_entries()
        if self.error_label:
            self.error_label.destroy()

        if self.customers_tree.selection():
            record = self.customers_tree.set(self.customers_tree.selection())

            self.id_entry.insert(tk.END, record[CUSTOMER_COLUMN_FULL[0]])
            self.full_name_entry.insert(tk.END, record[CUSTOMER_COLUMN_FULL[1]])
            self.email_entry.insert(tk.END, record[CUSTOMER_COLUMN_FULL[2]])

    def go_to_order_window(self):
        """Runs order window."""
        self.frame.destroy()
        self.entry_frame.destroy()
        self.listbox_frame.destroy()
        application = OrdersMenu()
        application.initialize_menu()

    def go_to_product_window(self):
        """Runs products window."""
        self.frame.destroy()
        self.entry_frame.destroy()
        self.listbox_frame.destroy()
        application = ProductsWindow()
        application.initialize_menu()

    def _export_from_mysql_to_postgres(self) -> None:
        export_data(self._mysql_engine, self._postgres_engine)

    def _export_from_postgres_to_sqlite(self) -> None:
        export_data(self._postgres_engine, self._sqlite_engine)


class ProductsWindow:
    def __init__(self) -> None:
        """Creates products window."""

        self._mysql_engine = mysql_engine_factory()
        self._product_repository = ProductRepository(self._mysql_engine)
        self._customer_repository = CustomerRepository(self._mysql_engine)
        self._order_repository = OrderRepository(self._mysql_engine)

        self._sqlite_engine = sqlite_engine_factory()
        self._postgres_engine = postgres_engine_factory()

        # frame for main buttons (customer,order,product)
        self.frame = tk.Frame(bg=BACKGROUND)
        self.frame.pack()
        # frame for all entries, function buttons and labels
        self.entry_frame = tk.Frame(bg=BACKGROUND)
        self.entry_frame.pack()
        # frame for listbox and scrollbar
        self.listbox_frame = tk.Frame(bg=BACKGROUND)
        self.listbox_frame.pack()

        # label that need to be defined in __init__ so functions can check if it exists and delete it
        self.error_label = tk.Label()

        self.product_tree = None
        self.product_description_entry = None
        self.product_name_entry = None
        self.product_price_entry = None

    def initialize_menu(self):
        """Initializes products window.

        Used in other functions repeatedly, that's why it's not in __init__"""
        # Destroying last frame and creating initializing menu
        self.frame.destroy()
        self.frame = tk.Frame(bg=BACKGROUND)
        self.frame.pack()

        self.entry_frame.destroy()
        self.entry_frame = tk.Frame(bg=BACKGROUND)
        self.entry_frame.pack()

        self.listbox_frame.destroy()
        self.listbox_frame = tk.Frame(bg=BACKGROUND)
        self.listbox_frame.pack()

        if self.error_label:
            self.error_label.destroy()

        # Create Main Buttons To Chose Which Table You Want To Add
        customer_button = tk.Button(
            self.frame,
            text="Customer",
            command=self.go_to_customer_window,
            width=30,
            bg=FOREGROUND,
        )
        customer_button.grid(row=0, column=0, pady=10)
        order_button = tk.Button(
            self.frame,
            text="Order",
            command=self.go_to_order_window,
            width=30,
            bg=FOREGROUND,
        )
        order_button.grid(
            row=0,
            column=1,
        )
        product_button = tk.Button(
            self.frame,
            text="Product",
            command=self.initialize_menu,
            width=30,
            bg=FOREGROUND,
        )
        product_button.grid(row=0, column=2)

        export_postgres_button = tk.Button(
            self.frame,
            text="Export to Postgres",
            command=self._export_from_mysql_to_postgres,
            width=30,
            bg=FOREGROUND,
        )
        export_postgres_button.grid(row=1, column=3)

        export_sqlite_button = tk.Button(
            self.frame,
            text="Export from Postgres to Sqlite",
            command=self._export_from_postgres_to_sqlite,
            width=30,
            bg=FOREGROUND,
        )
        export_sqlite_button.grid(row=2, column=3)

        # Create text box labels for Products
        product_ID_label = tk.Label(self.entry_frame, text="Product ID:", bg=BACKGROUND)
        product_ID_label.grid(row=0, column=0, sticky=tk.E)
        product_name_label = tk.Label(
            self.entry_frame, text="Product name:", bg=BACKGROUND
        )
        product_name_label.grid(row=1, column=0, sticky=tk.E)
        product_price_label = tk.Label(
            self.entry_frame, text="Product price:", bg=BACKGROUND
        )
        product_price_label.grid(row=2, column=0, sticky=tk.E)
        product_description_label = tk.Label(
            self.entry_frame, text="description(optional):", bg=BACKGROUND
        )
        product_description_label.grid(row=3, column=0, sticky=tk.E)

        # Create Entry Box for Products
        self.product_id_entry = tk.Entry(self.entry_frame, width=30, bg=FOREGROUND)
        self.product_id_entry.grid(row=0, column=1)
        self.product_name_entry = tk.Entry(self.entry_frame, width=30, bg=FOREGROUND)
        self.product_name_entry.grid(row=1, column=1)
        self.product_price_entry = tk.Entry(self.entry_frame, width=30, bg=FOREGROUND)
        self.product_price_entry.grid(row=2, column=1)
        self.product_description_entry = tk.Entry(
            self.entry_frame, width=30, bg=FOREGROUND
        )
        self.product_description_entry.grid(row=3, column=1)

        # buttons
        add_button = tk.Button(
            self.entry_frame,
            text="Add",
            command=self.add_product,
            width=20,
            bg=FOREGROUND,
        )
        add_button.grid(row=0, column=2, padx=20)
        update_button = tk.Button(
            self.entry_frame,
            text="Update",
            command=self.update_product,
            width=20,
            bg=FOREGROUND,
        )
        update_button.grid(row=2, column=2)
        clear_button = tk.Button(
            self.entry_frame,
            text="Clear",
            command=self.clear_product_entries,
            width=20,
            bg=FOREGROUND,
        )
        clear_button.grid(row=3, column=2)
        delete_button = tk.Button(
            self.entry_frame,
            text="Delete",
            command=self.delete_product,
            width=20,
            bg=FOREGROUND,
        )
        delete_button.grid(row=4, column=2)

        list_label = tk.Label(
            self.listbox_frame, text="list of products", width=100, bg=BACKGROUND
        )
        list_label.grid(row=0, column=0)

        # creating treeview
        self.product_tree = Treeview(
            self.listbox_frame, columns=PRODUCTS_COLUMNS, show="headings", height=10
        )
        self.product_tree.grid(row=1, column=0)

        for column_name, width in zip(PRODUCTS_COLUMNS, PRODUCT_COLUMNS_SIZE):
            self.product_tree.column(column_name, width=width, anchor=tk.CENTER)
            self.product_tree.heading(column_name, text=column_name)

        scrollbar = tk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL)
        scrollbar.configure(command=self.product_tree.set)
        self.product_tree.configure(yscrollcommand=scrollbar)
        self.product_tree.bind("<ButtonRelease-1>", self.get_selected_product)

        records = self._product_repository.get_all()

        for i, item in enumerate(records):
            self.product_tree.insert(
                "",
                index="end",
                iid=i,
                values=tuple(item[column] for column in PRODUCTS_COLUMNS),
            )

    def clear_product_entries(self):
        """Clears all entries."""
        if self.error_label:
            self.error_label.destroy()

        self.product_name_entry.delete(0, tk.END)
        self.product_price_entry.delete(0, tk.END)
        self.product_id_entry.delete(0, tk.END)
        self.product_description_entry.delete(0, tk.END)

    def add_product(self):
        """Adds new product, if all required entries are filled properly."""
        # deleting missing label from last add_order call, if it exists
        if self.error_label:
            self.error_label.destroy()

        # checking if all required entries are filled correctly
        if not self.product_name_entry.get():
            self.error_message("'product name' missing")
        elif (
                not is_float(self.product_price_entry.get())
                or float(self.product_price_entry.get()) < 1.0
        ):
            self.error_message("'product price' must be positive float")

        # if everything is filled
        else:
            self._product_repository.add(
                {
                    "name": self.product_name_entry.get(),
                    "price": self.product_price_entry.get(),
                    "description": self.product_description_entry.get(),
                }
            )

            # showing clear new window
            self.initialize_menu()

    def delete_product(self):
        """Deletes product, if selected by cursor."""
        if self.error_label:
            self.error_label.destroy()

        # checking if anything is selected from the listbox
        if not self.product_tree.selection():
            self.error_message("please select one from listbox.")
            return

        # finding selected Customer
        selected_record = self.product_tree.set(self.product_tree.selection())

        # window asking to delete
        answer = messagebox.askquestion("Are you sure?")
        if answer == "yes":
            self._product_repository.delete(selected_record[PRODUCTS_COLUMNS[0]])
            # refreshing all
            self.initialize_menu()

        # if there was no record with such id
        else:
            self.error_message("record not exists in database.")

    def update_product(self):
        """Updates product, if all required entries are filled properly."""
        if self.error_label:
            self.error_label.destroy()

        # checking if any record from LISTBOX is selected
        if not self.product_tree.selection():
            self.error_message("please select one from listbox.")
            return

        # checking if every required value for update is filled properly
        elif not self.product_name_entry.get():
            self.error_message("Can not update empty name.")
        elif not self.product_price_entry.get():
            self.error_message("Can not update empty price.")

        # everything is filled finally updating
        else:
            current_record = self.product_tree.set(self.product_tree.selection())
            self._product_repository.update(
                int(self.product_id_entry.get()),
                {
                    "full_name": self.product_name_entry.get(),
                    "email": self.product_price_entry.get(),
                    "description": self.product_description_entry,
                },
            )

            # refresh all
            self.initialize_menu()

    def get_selected_product(self, event):
        """Inserts selected product data into entries."""
        self.clear_product_entries()
        if self.error_label:
            self.error_label.destroy()
        try:
            if self.product_tree.selection():
                record = self.product_tree.set(self.product_tree.selection())
                self.product_id_entry.insert(tk.END, record[PRODUCTS_COLUMNS[0]])
                self.product_name_entry.insert(tk.END, record[PRODUCTS_COLUMNS[1]])
                self.product_price_entry.insert(tk.END, record[PRODUCTS_COLUMNS[2]])
                self.product_description_entry.insert(
                    tk.END, record[PRODUCTS_COLUMNS[3]]
                )

        except KeyError:
            pass

    def error_message(self, name):
        """Shows passed message in designated place

        Used to clear code and make it more readable as it is
        called multiple times."""
        if self.error_label:
            self.error_label.destroy()

        self.error_label = tk.Label(
            self.entry_frame, text=name, bg=BACKGROUND, fg=ERROR_COLOR
        )
        self.error_label.grid(row=4, column=1)

    def go_to_order_window(self):
        """Runs order window."""
        self.frame.destroy()
        self.entry_frame.destroy()
        self.listbox_frame.destroy()
        application = OrdersMenu()
        application.initialize_menu()

    def go_to_customer_window(self):
        """Runs customer window."""
        self.frame.destroy()
        self.entry_frame.destroy()
        self.listbox_frame.destroy()
        application = CustomersWindow()
        application.initialize_menu()

    def _export_from_mysql_to_postgres(self) -> None:
        export_data(self._mysql_engine, self._postgres_engine)

    def _export_from_postgres_to_sqlite(self) -> None:
        export_data(self._postgres_engine, self._sqlite_engine)


class OrdersMenu:
    def __init__(self):
        """Creates orders window."""
        self._mysql_engine = mysql_engine_factory()
        self._product_repository = ProductRepository(self._mysql_engine)
        self._customer_repository = CustomerRepository(self._mysql_engine)
        self._order_repository = OrderRepository(self._mysql_engine)

        self._sqlite_engine = sqlite_engine_factory()
        self._postgres_engine = postgres_engine_factory()

        # frame for main buttons (customer,order,product)
        self.frame = tk.Frame(bg=BACKGROUND)
        self.frame.pack()
        # frame for all entries, function buttons and labels
        self.entry_frame = tk.Frame(bg=BACKGROUND)
        self.entry_frame.pack()
        # frame for listbox and scrollbar
        self.orders_frame = tk.Frame(bg=BACKGROUND)
        self.orders_frame.pack()
        self.products_customers_frame = tk.Frame(bg=BACKGROUND)
        self.products_customers_frame.pack()

        # label that need to be defined in __init__ so functions can check if it exists and delete it
        self.error_label = tk.Label()

        self.order_tree = None
        self.product_tree = None
        self.customers_tree = None
        self.id_order = None
        self.id_product_entry = None
        self.id_customer_entry = None
        self.quantity_entry = None

    def initialize_menu(self):
        """Initializes orders window.

        Used in other functions repeatedly, that's why it's not in __init__"""
        # Destroying last frame and creating initializing menu
        self.frame.destroy()
        self.frame = tk.Frame(bg=BACKGROUND)
        self.frame.pack()

        self.entry_frame.destroy()
        self.entry_frame = tk.Frame(bg=BACKGROUND)
        self.entry_frame.pack()

        self.orders_frame.destroy()
        self.orders_frame = tk.Frame(bg=BACKGROUND)
        self.orders_frame.pack()

        self.products_customers_frame.destroy()
        self.products_customers_frame = tk.Frame(bg=BACKGROUND)
        self.products_customers_frame.pack()

        if self.error_label:
            self.error_label.destroy()

        # Create Main Buttons To Chose Which Table You Want To Add
        customer_button = tk.Button(
            self.frame,
            text="Customer",
            command=self.go_to_customer_window,
            width=30,
            bg=FOREGROUND,
        )
        customer_button.grid(row=0, column=0, pady=10)
        order_button = tk.Button(
            self.frame,
            text="Order",
            command=self.initialize_menu,
            width=30,
            bg=FOREGROUND,
        )
        order_button.grid(
            row=0,
            column=1,
        )
        product_button = tk.Button(
            self.frame,
            text="Product",
            command=self.go_to_product_window,
            width=30,
            bg=FOREGROUND,
        )
        product_button.grid(row=0, column=2)
        export_postgres_button = tk.Button(
            self.frame,
            text="Export to Postgres",
            command=self._export_from_mysql_to_postgres,
            width=30,
            bg=FOREGROUND,
        )
        export_postgres_button.grid(row=1, column=3)

        export_sqlite_button = tk.Button(
            self.frame,
            text="Export from Postgres to Sqlite",
            command=self._export_from_postgres_to_sqlite,
            width=30,
            bg=FOREGROUND,
        )
        export_sqlite_button.grid(row=2, column=3)

        # Create text box labels for Orders
        id_order_label = tk.Label(self.entry_frame, text="Order ID:", bg=BACKGROUND)
        id_order_label.grid(row=0, column=0, sticky=tk.E)
        id_customer_label = tk.Label(
            self.entry_frame, text="Customer ID:", bg=BACKGROUND
        )
        id_customer_label.grid(row=1, column=0, sticky=tk.E)
        id_product_label = tk.Label(self.entry_frame, text="Product ID:", bg=BACKGROUND)
        id_product_label.grid(row=2, column=0, sticky=tk.E)
        quantity_label = tk.Label(self.entry_frame, text="Quantity:", bg=BACKGROUND)
        quantity_label.grid(row=3, column=0, sticky=tk.E)

        # Create Entry Box for Orders
        self.id_order_entry = tk.Entry(self.entry_frame, width=30, bg=FOREGROUND)
        self.id_order_entry.grid(row=0, column=1)
        self.id_customer_entry = tk.Entry(self.entry_frame, width=30, bg=FOREGROUND)
        self.id_customer_entry.grid(row=1, column=1)
        self.id_product_entry = tk.Entry(self.entry_frame, width=30, bg=FOREGROUND)
        self.id_product_entry.grid(row=2, column=1)
        self.quantity_entry = tk.Entry(self.entry_frame, width=30, bg=FOREGROUND)
        self.quantity_entry.grid(row=3, column=1)

        # buttons
        add_button = tk.Button(
            self.entry_frame,
            text="Add",
            command=self.add_order,
            width=20,
            bg=FOREGROUND,
        )
        add_button.grid(row=1, column=2, padx=20)
        update_button = tk.Button(
            self.entry_frame,
            text="Update",
            command=self.update_order,
            width=20,
            bg=FOREGROUND,
        )
        update_button.grid(row=2, column=2)
        clear_button = tk.Button(
            self.entry_frame,
            text="Clear",
            command=self.initialize_menu,
            width=20,
            bg=FOREGROUND,
        )
        clear_button.grid(row=3, column=2)
        delete_button = tk.Button(
            self.entry_frame,
            text="Delete",
            command=self.delete_order,
            width=20,
            bg=FOREGROUND,
        )
        delete_button.grid(row=4, column=2)

        #  =================creating treeview (orders) =======================
        list_label = tk.Label(self.orders_frame, text="Orders", bg=BACKGROUND)
        list_label.grid(row=0, column=0)

        self.order_tree = Treeview(
            self.orders_frame, columns=ORDERS_COLUMNS, show="headings", height=8
        )
        self.order_tree.grid(row=1, column=0, padx=100)

        scrollbar_y = tk.Scrollbar(self.orders_frame, orient=tk.VERTICAL)
        scrollbar_y.configure(command=self.order_tree.set)
        scrollbar_x = tk.Scrollbar(self.orders_frame, orient=tk.HORIZONTAL)
        scrollbar_x.configure(command=self.order_tree.xview())
        self.order_tree.configure(yscrollcommand=scrollbar_y)
        self.order_tree.configure(xscrollcommand=scrollbar_x)

        for column_name, width in zip(ORDERS_COLUMNS, ORDER_COLUMNS_SIZE):
            self.order_tree.column(column_name, width=width, anchor=tk.CENTER)
            self.order_tree.heading(column_name, text=column_name)
            self.order_tree.bind("<ButtonRelease-1>", self.get_selected_order)

        #  =================creating treeview (products) =======================
        list_label1 = tk.Label(
            self.products_customers_frame, text="Products", width=25, bg=BACKGROUND
        )
        list_label1.grid(row=0, column=0)

        self.product_tree = Treeview(
            self.products_customers_frame,
            columns=PRODUCTS_COLUMNS,
            show="headings",
            height=8,
        )
        self.product_tree.grid(row=1, column=0, padx=10)
        scrollbar_y = tk.Scrollbar(self.products_customers_frame, orient=tk.VERTICAL)
        scrollbar_y.configure(command=self.product_tree.set)
        scrollbar_x = tk.Scrollbar(self.products_customers_frame, orient=tk.HORIZONTAL)
        scrollbar_x.configure(command=self.order_tree.xview())
        self.product_tree.configure(yscrollcommand=scrollbar_y)
        self.product_tree.configure(xscrollcommand=scrollbar_x)

        for column_name, width in zip(PRODUCTS_COLUMNS, PRODUCT_COLUMNS_SIZE):
            self.product_tree.column(column_name, width=width, anchor=tk.CENTER)
            self.product_tree.heading(column_name, text=column_name)

        #  =================creating treeview (customers) =======================
        list_label2 = tk.Label(
            self.products_customers_frame, text="Customers", width=25, bg=BACKGROUND
        )
        list_label2.grid(row=0, column=1)
        self.customers_tree = Treeview(
            self.products_customers_frame,
            columns=CUSTOMERS_COLUMNS,
            show="headings",
            height=8,
        )
        self.customers_tree.grid(row=1, column=1)

        scrollbar_y = tk.Scrollbar(self.products_customers_frame, orient=tk.VERTICAL)
        scrollbar_y.configure(command=self.customers_tree.set)
        scrollbar_x = tk.Scrollbar(self.products_customers_frame, orient=tk.HORIZONTAL)
        scrollbar_x.configure(command=self.order_tree.xview())
        self.customers_tree.configure(yscrollcommand=scrollbar_y)
        self.customers_tree.configure(xscrollcommand=scrollbar_x)

        for column_name, width in zip(CUSTOMERS_COLUMNS, CUSTOMER_COLUMNS_SIZE):
            self.customers_tree.column(column_name, width=width, anchor=tk.CENTER)
            self.customers_tree.heading(column_name, text=column_name)

        # # adding records from DB to List (orders)

        records = self._order_repository.get_all()

        for i, item in enumerate(records):
            self.order_tree.insert(
                "",
                index="end",
                iid=i,
                values=tuple(item[column] for column in ORDERS_COLUMNS),
            )

        # # adding records from DB to List (products)
        records = self._product_repository.get_all()

        for i, item in enumerate(records):
            self.product_tree.insert(
                "",
                index="end",
                iid=i,
                values=tuple(item[column] for column in PRODUCTS_COLUMNS),
            )

        # adding records from DB to List (customers)
        records = self._customer_repository.get_all()

        for i, item in enumerate(records):
            self.customers_tree.insert(
                "",
                index="end",
                iid=i,
                values=tuple(item[column] for column in CUSTOMER_COLUMN_FULL),
            )

    def add_order(self):
        """Place new order, if all required entries are filled."""
        # deleting missing label from last add_order call if it exists
        if self.error_label:
            self.error_label.destroy()

        # checking if all required entries are filled properly
        if not self.id_customer_entry.get():
            self.error_message("'id customer' missing")
        elif not self.id_product_entry.get():
            self.error_message("'id product' missing")
        elif (
                not is_integer(self.quantity_entry.get())
                or int(self.quantity_entry.get()) < 1
        ):
            self.error_message("'quantity' Must be an positive integer")

        else:
            try:
                self._order_repository.add(
                    {
                        "customer_id": self.id_customer_entry.get(),
                        "product_id": self.id_product_entry.get(),
                        "qty": self.quantity_entry.get(),
                    }
                )
            except InvalidDataError:
                self.error_message("Impossible to add order, because of invalid input.")
            except RelationError:
                self.error_message("Impossible to add order, because customer and/or product does not exists.")
            except InfrastructureException as error:
                self.error_message("Impossible to add order. Please refer logs for more information.")
                print(f"Error occurred: {error}")
            else:
                # showing clear new window
                self.initialize_menu()

    def update_order(self):
        """Updates customer, if all required entries are filled properly."""
        if self.error_label:
            self.error_label.destroy()

        # checking if any record from LISTBOX is selected
        if not self.order_tree.selection():
            self.error_message("please select one from listbox.")
            return

        # checking if every required value for update is filled properly
        elif not self.id_customer_entry.get():
            self.error_message("Can not update empty customer id.")
        elif not self.id_product_entry.get():
            self.error_message("Can not update empty product id.")

        # everything is filled finally updating
        else:
            try:
                self._order_repository.update(
                    int(self.id_order_entry.get()),
                    {
                        "customer_id": self.id_customer_entry.get(),
                        "product_id": self.id_product_entry.get(),
                        "qty": self.quantity_entry.get(),
                    },
                )
            except InvalidDataError:
                self.error_message("Impossible to add order, because of invalid input.")
            except RelationError:
                self.error_message("Impossible to add order, because customer and/or product does not exists.")
            except InfrastructureException as error:
                self.error_message("Impossible to add order. Please refer logs for more information.")
                print(f"Error occurred: {error}")
            else:
                # showing clear new window
                self.initialize_menu()

    def delete_order(self):
        """Deletes order, if selected by cursor."""
        if self.error_label:
            self.error_label.destroy()

        # checking if anything is selected from the listbox
        if not self.order_tree.selection():
            self.error_message("please select one from listbox.")
            return

        # finding selected Customer
        selected_record = self.order_tree.set(self.order_tree.selection())

        # window asking to delete
        answer = messagebox.askquestion("Are you sure?")
        if answer == "yes":
            self._order_repository.delete(selected_record[ORDERS_COLUMNS[0]])
            # refreshing all
            self.initialize_menu()

        # if there was no record with such id
        else:
            self.error_message("record not exists in database.")

    def get_selected_order(self, event):
        """Inserts selected product data into entries."""
        self.clear_order_entries()
        if self.error_label:
            self.error_label.destroy()
        try:
            if self.order_tree.selection():
                record = self.order_tree.set(self.order_tree.selection())
                self.id_order_entry.insert(tk.END, record[ORDERS_COLUMNS[0]])
                self.quantity_entry.insert(tk.END, record[ORDERS_COLUMNS[1]])
                self.id_customer_entry.insert(tk.END, record[ORDERS_COLUMNS[2]])
                self.id_product_entry.insert(tk.END, record[ORDERS_COLUMNS[3]])

        except KeyError:
            pass

    def clear_order_entries(self):
        """Clears all entries."""
        if self.error_label:
            self.error_label.destroy()

        self.id_order_entry.delete(0, tk.END)
        self.id_customer_entry.delete(0, tk.END)
        self.id_product_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)

    def error_message(self, name):
        """
            Shows passed message in designated place

            Used to clear code and make it more readable as it is
            called multiple times.
        """
        # deleting missing label from last add_order call if it exists
        if self.error_label:
            self.error_label.destroy()

        self.error_label = tk.Label(self.frame, text=name, bg=BACKGROUND, fg=ERROR_COLOR)
        self.error_label.grid(row=11, column=1)

    def go_to_customer_window(self):
        """Runs customer window."""
        self.frame.destroy()
        self.entry_frame.destroy()
        self.orders_frame.destroy()
        self.products_customers_frame.destroy()
        application = CustomersWindow()
        application.initialize_menu()

    def go_to_product_window(self):
        """Runs product window."""
        self.frame.destroy()
        self.entry_frame.destroy()
        self.orders_frame.destroy()
        self.products_customers_frame.destroy()
        application = ProductsWindow()
        application.initialize_menu()

    def _export_from_mysql_to_postgres(self) -> None:
        export_data(self._mysql_engine, self._postgres_engine)

    def _export_from_postgres_to_sqlite(self) -> None:
        export_data(self._postgres_engine, self._sqlite_engine)
