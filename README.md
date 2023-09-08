# RevPay : Payment Gateway API

This is a RESTful API for managing bank accounts, making differnt transactions, and checking account balances. It is built using Python and Flask, and it utilizes MySQL as the database for storing companies, cbank accounts and transaction data.

## Features

- Register businesses/companies.
- Create and manage bank accounts.
- Perform deposit and withdrawal transactions between accounts with different cases.
- Check account balances.
- Secure API endpoints using JWT authentication.
- Handle various validation checks, including account activation status, transaction types, and user authorization.

## Tech Stack 

- Flask
- Python
- MySQL

## API Endpoints

- /register - New user registration.
- /login: User login and JWT token generation.
- /add_account: Create a new bank account.
- /transactions: Perform deposit and withdrawal transactions.
- /balance/{account_id}: Get the balance of a specific account.

