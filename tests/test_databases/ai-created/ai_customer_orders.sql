-- Create the Customers table
CREATE TABLE Customers (
    CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT,
    Balance DECIMAL(10, 2),
    CreditLimit DECIMAL(10, 2)
);

-- Create the Products table
CREATE TABLE Products (
    ProductID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT,
    UnitPrice DECIMAL(10, 2)
);

-- Create the Orders table
CREATE TABLE Orders (
    OrderID INTEGER PRIMARY KEY AUTOINCREMENT,
    CustomerID INTEGER,
    AmountTotal DECIMAL(10, 2),
    ShippedDate DATE,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
);

-- Create the Items table
CREATE TABLE Items (
    ItemID INTEGER PRIMARY KEY AUTOINCREMENT,
    OrderID INTEGER,
    ProductID INTEGER,
    Quantity INTEGER,
    Amount DECIMAL(10, 2),
    UnitPrice DECIMAL(10, 2),
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID),
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
);


-- Insert sample customers
INSERT INTO Customers (Name, Balance, CreditLimit) VALUES
    ('Customer 1', 1000.00, 2000.00),
    ('Customer 2', 1500.00, 3000.00);

-- Insert sample products
INSERT INTO Products (Name, UnitPrice) VALUES
    ('Product A', 10.00),
    ('Product B', 20.00);
