-- ============================================================
-- SLOW QUERIES — These are the four queries you must optimize.
-- Each query is labeled Q1 through Q4.
-- ============================================================

-- Q1: Top customers by spending in Q1 2024
-- Business context: Sales team needs a report of highest-value customers
-- from the first quarter to plan outreach campaigns.
SELECT c.customer_id, c.name, c.email, SUM(oi.quantity * oi.unit_price) as total_spent
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_date BETWEEN '2024-01-01' AND '2024-03-31'
  AND o.status = 'completed'
GROUP BY c.customer_id, c.name, c.email
HAVING SUM(oi.quantity * oi.unit_price) > 500
ORDER BY total_spent DESC;

-- Q2: Pending orders from October 2024 onward with item details
-- Business context: Operations team needs to see what pending orders
-- are in the pipeline to allocate warehouse resources.
SELECT o.order_id, o.order_date, o.region,
       p.name as product_name, oi.quantity, oi.unit_price
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'pending'
  AND o.order_date >= '2024-10-01'
ORDER BY o.order_date DESC;

-- Q3: Product performance report for Electronics category
-- Business context: Product managers need to see which electronics
-- products have strong reviews and sales to guide inventory decisions.
SELECT p.product_id, p.name, p.category,
    (SELECT AVG(r.rating)::numeric(3,2) FROM reviews r WHERE r.product_id = p.product_id) as avg_rating,
    (SELECT SUM(oi.quantity * oi.unit_price) FROM order_items oi WHERE oi.product_id = p.product_id) as total_revenue,
    (SELECT COUNT(DISTINCT oi2.order_id) FROM order_items oi2
     JOIN orders o ON oi2.order_id = o.order_id
     WHERE oi2.product_id = p.product_id AND o.order_date >= '2024-01-01') as orders_this_year
FROM products p
WHERE p.category = 'Electronics'
  AND (SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.product_id) >= 3
ORDER BY total_revenue DESC NULLS LAST
LIMIT 20;

-- Q4: High-priority orders needing attention
-- Business context: Customer success team needs a list of orders that
-- require immediate follow-up — either high-value pending orders or
-- long-standing pending orders from enterprise customers.
SELECT DISTINCT o.order_id, o.order_date, o.status, o.region,
       c.name as customer_name, c.tier,
       (SELECT SUM(oi2.quantity * oi2.unit_price) FROM order_items oi2 WHERE oi2.order_id = o.order_id) as order_total
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'pending'
  AND (
    (SELECT SUM(oi3.quantity * oi3.unit_price) FROM order_items oi3 WHERE oi3.order_id = o.order_id) > 5000
    OR
    (c.tier = 'enterprise' AND o.order_date < '2024-10-01')
  )
ORDER BY o.order_date;
