# TradeSphere – Stock Trading Platform

## Project Overview

TradeSphere is a simplified stock trading platform designed to demonstrate the core concepts of system design used in real-world trading applications such as Zerodha and Robinhood.

The platform allows users to place buy and sell orders, execute trades through a matching engine, manage portfolios, maintain transaction records, and generate audit logs. The project is implemented using Python, Flask, SQLite, HTML, CSS, and JavaScript.

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Snehahande05/TradeSphere.git
cd TradeSphere
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Dependencies

The project uses the following technologies and libraries:

* Python 3.x
* Flask
* SQLite
* HTML5
* CSS3
* JavaScript
* Chart.js

Install all required dependencies using:

```bash
pip install -r requirements.txt
```

---

## Execution Steps

### Run the Flask Application

```bash
python3 app.py
```

The application will start on:

```text
http://localhost:5001
```

Open the above URL in your browser.

### Alternative Port

If required:

```bash
PORT=5001 python3 app.py
```

---

## Additional Project Details

### Features

* User Authentication
* Stock Market Dashboard
* Buy and Sell Order Placement
* Order Validation
* Trade Matching Engine
* Trade Execution
* Portfolio Management
* Audit Logging
* SQLite Database Integration
* Flask REST APIs
* Responsive Web Interface

### Technology Stack

* Frontend: HTML, CSS, JavaScript
* Backend: Flask (Python)
* Database: SQLite
* APIs: REST APIs

### Database Tables

* Users
* Stocks
* Orders
* Trades
* Portfolio
* Audit Logs

---

## GitHub Repository

Repository Link:

https://github.com/Snehahande05/TradeSphere
