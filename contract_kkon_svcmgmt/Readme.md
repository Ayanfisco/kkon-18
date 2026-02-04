# KKONTech Service Management
A custom module created to  enable recurring broadband services.

## Basic Usage

1. Enable Product variants
  - Go to Settings -> Sales -> Product Catalog.
  - Check  the box beside "Variants".
  - Save

2. Create a product for your broadband service
  - Product Type: Service
  - Sale Price: N0
  - Under "Attributes & Variants"
    - Create an attribute named "bandwidth"
    - Create "Values" for bandwidth as needed (10Mbps, 20Mbps, etc.)
    - To configure bandwidth prices 
      - Click Configure
      - Enter prices for the various bandwidth options

3. Create Service Templates
  - Go to Invoicing -> Configuration -> Service Templates
  - Enter a Name
  - Select a Price List
  - Add a Product (one of the variants created above)
  - Under Service Template Lines
    - Select Product
    - Check "Auto-Price"
    - Edit Description as desired - this will appear on the invoice.  
      eg. Broadband service (30Mbps) #START# - #END# > This will display the service Start and End dates on the invoice.
    - Save and Close

4. Creating Services for Customers
  - Go to Either:
    - Sales -> Orders -> Services -> New  
    - Invoicing -> Customers -> Services -> New
    - Customer's Profile -> Sale Service Button -> New
  - Select a Customer
  - Select a Service Template
  - Select Payment Terms
  - If the service begins at a later date:
    - Set the Start Date (Date Start)
    - Set the Date of Next Invoice to the Start Date
  - Save 
  - The first invoice will be created automatically
  - Confirm the Invoice and send to Customer as required

  - Check "Enable"
  - Save

  - Click "Sync" to verify the account has been provisioned
    - If "Activated" is checked => IP address has been provisioned on the router.

5. Activate Portal Access for a Customer
  - Go to the Customer's Profile
  - Go to  Actions -> Grant Portal Access -> GRANT ACCESS
  - An "Invite" will be sent the customer's email address

6. To See Portal Users
  - Go to Settings  -> Manage Users -> Uncheck "Internal Users"
  - You can set or change the user's password here
    - Select the User -> Actions -> Change Password


## Changelog
#### 06-18-2024: Initial version

1. Settings
  - Settings: Settings > Invoicing/Accounting > Service Management API
  - Added option to disable/enable account provisioning with the API (default=disabled)
  - Added option to disable/enable email notifications (default=disabled)
  - Exposed the API credentials (URL, email & password)

2. Email Notifications
  - Welcome Email << Service creation
  - Service Activation Emai <- Service enabled
  - Service suspension Email <- Service disabled
  - Service Termination Email <- Service deleted
  - Payment confirmation Email <- Invoice paid
  - Payment Reminder Email <- 7, 3, 2, 1 days before due date
  - Overdue Payment Email <- 2, 7, 14 days after due date
  - New Invoice Email <- Invoice creation

3. Invoice Generation
  - Invoices are generated automatically @ service creation
  - Invoices are generated 15 days before service expires
  - FIX: First invoice is generated when the dates are altered


#### 07-17-2024:
- Disabled IP address entry in Odoo


#### 07-26-2024:
  - Payment Reminder Email <- 5, 10 days before due date
  - Overdue Payment Email <- 1 day after due date
  - Link to the customer portal included in the email templates
