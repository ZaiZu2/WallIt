
CREATE TABLE transactions(
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    info TEXT,
    title TEXT,
    amount NUMERIC(15,6) NOT NULL,
    currency TEXT NOT NULL,
    src_amount NUMERIC(15,6),
    src_currency TEXT,
    transaction_date TIMESTAMP NOT NULL,
    place TEXT,
    category TEXT,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bank_id BIGINT NOT NULL REFERENCES banks(id) ON DELETE SET NULL,

    CONSTRAINT upsert_constraint UNIQUE (amount, currency, transaction_date, user_id, bank_id);
)

CREATE TABLE users(
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    username TEXT UNIQUE NOT NULL,
    passcode TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL
);

CREATE TABLE banks(
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    bank_name TEXT UNIQUE NOT NULL
);