
CREATE TABLE transactions(
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    info TEXT,
    title TEXT,
    dir SMALLINT NOT NULL,
    amount NUMERIC(15,6) NOT NULL,
    currency TEXT NOT NULL,
    src_amount NUMERIC(15,6),
    src_currency TEXT,
    transaction_date TIMESTAMP NOT NULL,
    place TEXT,
    category TEXT);

ALTER TABLE transactions ADD CONSTRAINT dir_values CHECK (dir = 1 OR dir = -1);


