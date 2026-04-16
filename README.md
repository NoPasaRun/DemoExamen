# DemoExamen - Order and Product Management System

A desktop application for managing a database of products and orders with support for different user roles. Built with Python using PySide6 for the graphical interface and SQLAlchemy for database operations. Features an integrated micro-framework (**pyside6_scaffold**) for automatic form generation from SQLAlchemy ORM models.

## 📋 Project Overview

**DemoExamen** is an order and product management system that enables:
- Browse product catalog with filtering and sorting capabilities
- Manage orders (create, edit, delete)
- Manage products and their characteristics (admin only)
- Control access based on user roles (Administrator, Manager, Guest)
- Handle product image uploads
- Import data from Excel files
- Leverage automatic form generation through the **pyside6_scaffold** micro-framework

## 🏗️ Project Architecture

### Module Structure

```
DemoExamen/
├── module1.py                 # ORM models and database operations
├── module2/
│   ├── __init__.py           # Global variables and base classes
│   └── app.py                # Main application and primary windows
├── module3.py                # Components for product management
├── module4.py                # Components for order management
├── pyside6_scaffold/         # Micro-framework for automatic form generation
│   ├── core.py              # Core classes and protocols
│   ├── forms.py             # PysideForm and form utilities
│   ├── widgets.py           # Custom widgets (PysideField, PysideSelectable, etc.)
│   ├── registry.py          # Type-to-widget registry and type converters
│   └── example.py           # Usage example
├── import/                   # Data and resource files
└── requirements.txt          # Project dependencies
```

### Core Components

#### **module1.py** - Data Layer
Contains SQLAlchemy ORM models:
- `Company` - Companies (manufacturers and suppliers)
- `Product` - Products with price, quantity, and discount information
- `User` - System users with different roles
- `Address` - Delivery addresses
- `Order` - Orders with delivery information
- `OrderItem` - Products in orders

Also contains:
- PostgreSQL database connection settings
- Data import functions from Excel files (`get_data`, `save_data`)
- `main()` function for database initialization and test data loading

#### **module2** - Base GUI Components
- `Global` - Global variables (current window, authenticated user)
- `BaseWindow` - Base class for all application windows
- `AuthWindow` - Login window with guest login support
- `ProductsWindow` - Main window with product list
- `msg()` - Function for displaying user messages

#### **module3.py** - Product Management Components
- `BackwardMixin` - Mixin for navigation between windows (back button)
- `FilterProductWidget` - Widget for product filtering and sorting
  - Search by name, description, article, category
  - Filter by suppliers
  - Sort by warehouse quantity
- `ProductForm` - Form for creating/editing products
- `ImageUploader` - Image uploader with preview
- `delete_product()` - Product deletion function with validation

#### **module4.py** - Order Management Components
- `OrderWindow` - Main window with order list
- `OrderForm` - Form for creating/editing orders
  - Add/remove products from order
  - Select delivery address
  - Set creation and delivery dates
- `OrderWidget` - Visual representation of order in list
- `OrderItemWidget` - Widget for editing order item

## 🎯 pyside6_scaffold Micro-Framework

A powerful micro-framework for automatically generating PySide6 forms from SQLAlchemy ORM models. It eliminates boilerplate code by introspecting your database models and creating fully functional forms with minimal effort.

### Key Features

- **Automatic Form Generation** - Generate complete CRUD forms from SQLAlchemy models
- **Type Conversion** - Automatically converts SQLAlchemy types to appropriate PySide6 widgets
- **Relationship Handling** - Support for one-to-many and many-to-many relationships
- **Custom Validators** - Built-in validators for different data types
- **Field Metadata** - Uses SQLAlchemy `Column.info` for customization
- **Extensible Registry** - Type registry pattern for custom type converters

### Architecture

#### **core.py** - Core Classes
- `Message` - Enum for different message types (Information, Warning, Critical, Question)
- `Model` - Protocol defining the interface for SQLAlchemy models

#### **forms.py** - Form Generation
- `PysideForm` - Main form generator class
  - Introspects SQLAlchemy models
  - Generates form fields and layouts
  - Handles data validation
  - Manages relationships (single and multiple select)
  - Creates and persists instances
  
- `open_sub_window()` - Convenience function to open forms in dialogs or main windows

Key methods:
- `layout()` - Returns the complete form layout
- `save()` - Validates and saves form data to database
- `instance()` - Creates a model instance from form data
- `null_check()` - Validates required fields

#### **widgets.py** - Custom Widgets
- `PysideWidget` - Protocol/interface for all form widgets
- `PysideField` - Standard input field widget
  - Handles String, Integer, Float, Boolean, DateTime types
  - Supports default values
  - Uses type registry for widget creation
  
- `PysideSelectable` - Dropdown/combo box for foreign key relationships
  - Single selection from related objects
  - Queries database for available choices
  - Supports in-line creation of new related objects
  
- `PysideMultipleSelectable` - Multiple selection widget for many-to-many relationships
  - Checkboxes for each related object
  - Scrollable list for many items
  - Supports adding new related objects

#### **registry.py** - Type Registry
The `SqlToPysideRegistry` is a singleton that maps SQLAlchemy types to PySide6 widgets:

**Default Type Converters:**
- `String` → `QLineEdit`
- `Integer` → `QLineEdit` with `QIntValidator`
- `Float` → `QLineEdit` with `QDoubleValidator`
- `Boolean` → `QCheckBox`
- `DateTime` → `QDateTimeEdit`

Custom converters can be registered using the `@type_registry.register()` decorator.

### Using pyside6_scaffold

#### Basic Usage

```python
from pyside6_scaffold.forms import open_sub_window
from module1 import Session, Product

# Open a form for creating/editing a Product
with Session() as session:
    window = open_sub_window(Product, parent=None, session=session)
```

#### Programmatic Form Creation

```python
from pyside6_scaffold.forms import PysideForm
from module1 import Product, Session

with Session() as session:
    form = PysideForm(Product, session=session)
    layout = form.layout()
    
    # Add layout to your widget/window
    your_widget.setLayout(layout)
    
    # When user clicks save:
    instance = form.save()  # Returns the saved instance or False
```

#### Using Default Values

```python
form = PysideForm(
    Product, 
    session=session,
    name="Default Product Name",
    price=99.99,
    quantity=100
)
```

#### Field Customization via SQLAlchemy Column.info

The framework uses the `info` parameter of SQLAlchemy columns to customize form behavior:

```python
from sqlalchemy import Column, String, Float, Integer

class Product(Base):
    articul = Column(
        String, 
        primary_key=True,
        info={"label": "Product Article"}
    )
    
    price = Column(
        Float,
        info={
            "label": "Price (USD)",
            "range": (0, 10000),      # min, max values
            "decimals": 2             # decimal places
        }
    )
    
    quantity = Column(
        Integer,
        info={
            "label": "Stock Quantity",
            "range": (0, 100000)
        }
    )
    
    supplier = relationship(
        "Company",
        info={
            "label": "Supplier",
            "choices": lambda session: Company.filter(session)
        }
    )
```

### How It Works

1. **Model Introspection** - Uses SQLAlchemy's `inspect()` to analyze the model
2. **Field Generation** - Iterates through columns and creates appropriate widgets:
   - Regular columns → `PysideField`
   - Foreign keys (relationships) → `PysideSelectable`
   - Many-to-many relationships → `PysideMultipleSelectable`
3. **Validation** - Checks for required fields and data types
4. **Persistence** - Uses `session.merge()` to save changes to the database
5. **Error Handling** - Displays validation errors via message dialogs

### Example from the Project

Looking at **module2/app.py**, `AuthWindow` demonstrates manual form creation without using the scaffold. However, the scaffold could simplify this significantly:

```python
# Without scaffold (current implementation)
self.loginInput = QLineEdit()
self.loginInput.setPlaceholderText("Enter login")
self.passwordInput = QLineEdit()
self.passwordInput.setPlaceholderText("Enter password")

# With scaffold
form = PysideForm(User, session=session)
```

### Extending the Registry

Add custom type converters:

```python
from pyside6_scaffold.registry import type_registry
from PySide6.QtWidgets import QSpinBox

@type_registry.register(MyCustomType)
def as_custom_type(field: 'PysideField'):
    widget = QSpinBox()
    widget.setMinimum(field.column.info.get("min", 0))
    widget.setMaximum(field.column.info.get("max", 100))
    return widget
```

## 🔐 User Roles

| Role | Capabilities |
|------|------------|
| **Administrator** | Full access: view products, create/edit/delete products and orders, user management |
| **Manager** | View products with filtering, manage orders |
| **Guest** | View product catalog only |

## 📦 Dependencies

```
PySide6==6.10.1           # GUI framework
SQLAlchemy==2.0.44        # ORM
psycopg2-binary==2.9.11   # PostgreSQL driver
openpyxl==3.1.5           # Excel file handling
pandas==2.3.3             # Data processing
Pillow==12.1.0            # Image handling
matplotlib==3.10.8        # Plotting library
numpy==2.4.1              # Numerical computations
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL (must be running and configured)
- pip

### Step-by-Step Installation

#### 1. Download Demo Data

**Linux:**
```bash
curl https://gearstore.site/media/import.tar -O import.tar && tar -xf import.tar && rm import.tar
```

**Windows (Command Prompt):**
```cmd
curl -L "https://gearstore.site/media/import.tar" -o import.tar && tar -xf import.tar && del import.tar
```

#### 2. Create Virtual Environment and Install Dependencies

**Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

**Windows:**
```cmd
python -m venv venv
.\venv\Scripts\activate
pip3 install -r requirements.txt
```

#### 3. Configure Database Connection

Edit the connection string in `module1.py` (lines 19-21):

```python
engine = create_engine("postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")
```

Change the values:
- `username` - your PostgreSQL username
- `password` - your PostgreSQL password
- `host` - database host (usually `localhost`)
- `port` - database port (usually `5432`)
- `database` - database name

#### 4. Initialize Database

```bash
python -m module1
```

This will create all necessary tables and load test data from the `import/` folder.

#### 5. Run the Application

```bash
python -m module2.app
```

### Login Credentials (after DB initialization)

```
Login: 94d5ous@gmail.com
Password: uzWC67
Role: Administrator
```

To login as a guest, click the "Login as Guest" button.

## 📊 Database Schema

### `company` Table
- `name` (STRING, PK) - Company name

### `product` Table
- `articul` (STRING, PK) - Product article/SKU
- `name` (STRING) - Product name
- `measure_type` (STRING) - Unit of measurement
- `price` (FLOAT) - Product price
- `supplier_name` (STRING, FK) - Supplier
- `man_name` (STRING, FK) - Manufacturer
- `category` (STRING) - Product category
- `discount` (FLOAT) - Discount percentage
- `quantity` (INTEGER) - Stock quantity
- `description` (STRING) - Product description
- `photo` (STRING) - Path to product photo

### `user` Table
- `id` (INTEGER, PK) - User ID
- `role` (STRING) - User role (Administrator/Manager/Guest)
- `fio` (STRING) - Full name
- `login` (STRING, UNIQUE) - Login username
- `password` (STRING) - Password
- `is_active` (BOOLEAN) - Active status

### `address` Table
- `id` (INTEGER, PK) - Address ID
- `description` (STRING) - Address description

### `order` Table
- `articul` (INTEGER, PK) - Order article/number
- `created_at` (DATETIME) - Order creation date
- `deliver_at` (DATETIME) - Delivery date
- `address_id` (INTEGER, FK) - Delivery address
- `user_id` (INTEGER, FK) - User who created the order
- `code` (INTEGER) - Delivery code
- `status` (STRING) - Order status (New/Completed)

### `order_item` Table
- `id` (INTEGER, PK) - Order item ID
- `order_articul` (INTEGER, FK) - Order article
- `product_articul` (STRING, FK) - Product article
- `quantity` (INTEGER) - Item quantity

## 🎨 Core Features

### Product Browsing
- List all products with images and price information
- Display discounts with visual highlighting
- Stock availability status

### Product Filtering
- **Search** by name, description, article, category
- **Filter by suppliers** from dropdown
- **Sort by quantity** in stock (ascending/descending)

### Product Management (Administrators Only)
- Create new products
- Edit existing products
- Delete products (with relationship validation)
- Upload and modify product photos
- Set discounts

### Order Management (Managers and Administrators)
- View all orders
- Create new orders
- Add/remove products from orders
- Edit order status
- Set delivery address and dates

## ⚠️ Important Notes

1. **Windows commands must be executed in Command Prompt, NOT PowerShell**
2. **Configure PostgreSQL connection settings in module1.py before running**
3. **Ensure PostgreSQL is running before database initialization**
4. **The `import/` folder must contain all required data files and images**
5. **The pyside6_scaffold is a micro-framework for reducing boilerplate - not currently used for all forms in this project, but demonstrates best practices**

## 🛠️ Deployment on a New Machine

```bash
# 1. Clone the repository
git clone <repository_url>
cd DemoExamen

# 2. Download data
curl https://gearstore.site/media/import.tar -O import.tar && tar -xf import.tar && rm import.tar

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip3 install -r requirements.txt

# 5. Configure database settings in module1.py

# 6. Initialize database
python -m module1

# 7. Run the application
python -m module2.app
```

## 📝 License

Educational project.

## 👤 Author

Bogdan

