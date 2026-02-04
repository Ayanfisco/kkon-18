# Stock Location Reports Module

## Overview

This Odoo 16 module adds a "Stock Location Reports" menu under the Reports section that allows users to dynamically switch between different stock locations and view their current stock information.

## Features

* **Dynamic Location Selection** : Dropdown field to select any internal stock location
* **Current Stock View** : Shows the same tree view as clicking "Current Stock" on a location
* **Reports Integration** : Accessible via Inventory → Reports → Stock Location Reports
* **User-Friendly Interface** : Clean form with instructions and action buttons

## Module Structure

```
stock_location_reports/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── stock_location_report.py
├── views/
│   ├── menu_views.xml
│   └── stock_location_report_views.xml
├── security/
│   └── ir.model.access.csv
└── README.md
```

## Installation

1. Copy the `stock_location_reports` folder to your Odoo addons directory
2. Update the apps list in Odoo
3. Install the "Stock Location Reports" module

## Usage

1. Go to **Inventory → Reports → Stock Location Reports**
2. Select a stock location from the dropdown
3. Click "View Current Stock" to see the inventory for that location
4. Use "Refresh" to update the report

## Technical Details

* **Model** : `stock.location.report` (TransientModel)
* **Views** : Form view with location selector and action buttons
* **Security** : Access rights for stock users and managers
* **Dependencies** : Extends the stock module

## Compatibility

* Odoo 16.0
* Requires stock module

## Author

MOB - Ifeanyi Nneji
