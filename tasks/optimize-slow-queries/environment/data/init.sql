-- Schema and seed data for the e-commerce analytics database.
-- Data is generated deterministically using setseed() so query results
-- are reproducible across builds.

-- ============================================================
-- SCHEMA
-- ============================================================

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(200) NOT NULL,
    signup_date DATE NOT NULL,
    tier VARCHAR(20) NOT NULL,
    country VARCHAR(50) NOT NULL
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,
    region VARCHAR(50) NOT NULL
);

CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL
);

CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    customer_id INT NOT NULL,
    rating INT NOT NULL,
    review_date TIMESTAMP NOT NULL
);

-- ============================================================
-- SEED DATA
-- ============================================================

SELECT setseed(0.42);

-- 50,000 customers
INSERT INTO customers (name, email, signup_date, tier, country)
SELECT
    'Customer ' || i,
    'user' || i || '@' ||
        (ARRAY['gmail.com','yahoo.com','techcorp.com','megasoft.io','outlook.com',
               'fastmail.net','proton.me','company.org','startup.co','enterprise.biz'])
            [1 + floor(random() * 10)::int],
    '2020-01-01'::date + (random() * 1600)::int,
    (ARRAY['free','basic','premium','enterprise'])
        [1 + floor(random() * 4)::int],
    (ARRAY['US','UK','Germany','France','Japan','Brazil','Canada','Australia','India','Mexico',
           'Spain','Italy','Netherlands','Sweden','Singapore'])
        [1 + floor(random() * 15)::int]
FROM generate_series(1, 50000) AS i;

-- 5,000 products across 8 categories
INSERT INTO products (name, category, subcategory, price, created_at)
SELECT
    (ARRAY['Pro','Ultra','Basic','Elite','Max','Mini','Smart','Eco','Flex','Prime'])
        [1 + floor(random() * 10)::int]
    || ' ' ||
    (ARRAY['Widget','Gadget','Device','Module','Unit','Kit','Set','Pack','Tool','Gear'])
        [1 + floor(random() * 10)::int]
    || ' ' || i,
    (ARRAY['Electronics','Clothing','Home','Sports','Books','Food','Toys','Office'])
        [1 + floor(random() * 8)::int],
    (ARRAY['SubA','SubB','SubC','SubD','SubE'])
        [1 + floor(random() * 5)::int],
    round((10 + random() * 990)::numeric, 2),
    '2021-01-01'::timestamp + (random() * 1200)::int * interval '1 day'
FROM generate_series(1, 5000) AS i;

-- 500,000 orders spread across 2023-2024
INSERT INTO orders (customer_id, order_date, status, region)
SELECT
    1 + floor(random() * 50000)::int,
    '2023-01-01'::timestamp + (random() * 730)::int * interval '1 day'
        + (random() * 86400)::int * interval '1 second',
    (ARRAY['completed','completed','completed','completed',
           'pending','pending','cancelled','refunded'])
        [1 + floor(random() * 8)::int],
    (ARRAY['North America','Europe','Asia','South America','Oceania','Africa'])
        [1 + floor(random() * 6)::int]
FROM generate_series(1, 500000) AS i;

-- 1,500,000 order items (3 items per order on average)
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT
    1 + floor(random() * 500000)::int,
    1 + floor(random() * 5000)::int,
    1 + floor(random() * 5)::int,
    round((5 + random() * 500)::numeric, 2)
FROM generate_series(1, 1500000) AS i;

-- 100,000 reviews
INSERT INTO reviews (product_id, customer_id, rating, review_date)
SELECT
    1 + floor(random() * 5000)::int,
    1 + floor(random() * 50000)::int,
    1 + floor(random() * 5)::int,
    '2023-06-01'::timestamp + (random() * 550)::int * interval '1 day'
FROM generate_series(1, 100000) AS i;

-- Run ANALYZE so PostgreSQL has accurate statistics for query planning
ANALYZE;
