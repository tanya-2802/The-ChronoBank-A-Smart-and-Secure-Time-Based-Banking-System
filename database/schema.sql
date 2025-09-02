-- Create database
CREATE DATABASE chronobank;

-- Connect to the database
\c chronobank;

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reputation_score FLOAT DEFAULT 100.0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create account_types table
CREATE TABLE account_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    min_balance INTEGER DEFAULT 0,
    interest_rate FLOAT DEFAULT 0.0,
    transaction_limit INTEGER DEFAULT 1000
);
    
-- Create accounts table
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    account_type_id INTEGER NOT NULL REFERENCES account_types(id),
    account_number VARCHAR(20) UNIQUE NOT NULL,
    balance INTEGER NOT NULL DEFAULT 0, -- Time in seconds
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, OVERDRAWN, FROZEN
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT positive_balance CHECK (balance >= 0)
);

-- Create transaction_types table
CREATE TABLE transaction_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Create transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_type_id INTEGER NOT NULL REFERENCES transaction_types(id),
    source_account_id INTEGER REFERENCES accounts(id),
    destination_account_id INTEGER REFERENCES accounts(id),
    amount INTEGER NOT NULL, -- Time in seconds
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING, COMPLETED, FAILED, REVERSED
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    reference_code VARCHAR(50) UNIQUE NOT NULL
);

-- Create loans table
CREATE TABLE loans (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    amount INTEGER NOT NULL, -- Time in seconds
    interest_rate FLOAT NOT NULL,
    term_days INTEGER NOT NULL,
    remaining_amount INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, PAID, DEFAULTED
    repayment_strategy VARCHAR(20) NOT NULL DEFAULT 'FIXED', -- FIXED, DYNAMIC
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP NOT NULL
);

-- Create investments table
CREATE TABLE investments (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    amount INTEGER NOT NULL, -- Time in seconds
    interest_rate FLOAT NOT NULL,
    term_days INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, MATURED, WITHDRAWN
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    maturity_date TIMESTAMP NOT NULL
);

-- Create notifications table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create fraud_alerts table
CREATE TABLE fraud_alerts (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    transaction_id INTEGER REFERENCES transactions(id),
    risk_score FLOAT NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN', -- OPEN, RESOLVED, FALSE_POSITIVE
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Create audit_logs table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert default account types
INSERT INTO account_types (name, description, min_balance, interest_rate, transaction_limit)
VALUES 
    ('BasicTimeAccount', 'Standard account for everyday time transactions', 0, 0.0, 1000),
    ('InvestorAccount', 'Account for time investments with higher interest rates', 500, 0.05, 5000),
    ('LoanAccount', 'Account for borrowing time with flexible repayment options', 0, 0.08, 2000),
    ('SavingsAccount', 'High-interest account for saving time with bonus rewards', 3600, 0.07, 3000);

-- Insert default transaction types
INSERT INTO transaction_types (name, description)
VALUES 
    ('Transfer', 'Transfer time between accounts'),
    ('Deposit', 'Add time to an account'),
    ('Withdrawal', 'Remove time from an account'),
    ('Loan', 'Borrow time with interest'),
    ('Investment', 'Invest time for future returns'),
    ('Interest', 'Interest earned on investments or charged on loans'),
    ('Fee', 'Service fees charged by the ChronoBank');
