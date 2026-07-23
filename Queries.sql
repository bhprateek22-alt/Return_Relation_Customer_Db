#True Profitability & Net Revenue After Returns
SELECT 
    p.product_id,
    p.product_name,
    SUM(oi.quantity * oi.unit_price) AS gross_revenue,
    COALESCE(SUM(ri.quantity * oi.unit_price), 0) AS returned_value,
    SUM(oi.quantity * oi.unit_price) - COALESCE(SUM(ri.quantity * oi.unit_price), 0) AS net_revenue,
    ROUND(
        (COALESCE(SUM(ri.quantity * oi.unit_price), 0) / NULLIF(SUM(oi.quantity * oi.unit_price), 0)) * 100, 
        2
    ) AS return_value_percentage
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
LEFT JOIN return_items ri ON oi.order_item_id = ri.order_item_id
LEFT JOIN returns r ON ri.return_id = r.return_id AND r.refund_status = 'processed'
WHERE o.status != 'cancelled'
GROUP BY p.product_id, p.product_name
ORDER BY net_revenue DESC;
#Customer Lifetime Value (CLV) & Return Behavior
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    c.email,
    COUNT(DISTINCT o.order_id) AS total_orders_placed,
    SUM(o.total_amount) AS total_gross_spend,
    COALESCE(SUM(r.refund_amount), 0) AS total_refunded,
    (SUM(o.total_amount) - COALESCE(SUM(r.refund_amount), 0)) AS net_customer_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN returns r ON o.order_id = r.order_id AND r.refund_status = 'processed'
WHERE o.status != 'cancelled'
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
ORDER BY net_customer_value DESC
LIMIT 20;
#Inventory Turnover & Stockout Risk Alert
SELECT 
    p.product_id,
    p.product_name,
    p.stock_quantity AS current_stock,
    COALESCE(SUM(oi.quantity), 0) AS total_units_sold,
    p.price,
    CASE 
        WHEN p.stock_quantity = 0 THEN 'OUT OF STOCK'
        WHEN p.stock_quantity < (COALESCE(SUM(oi.quantity), 0) * 0.20) THEN 'CRITICAL LOW'
        ELSE 'OK'
    END AS stock_health_status
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, p.stock_quantity, p.price
ORDER BY current_stock ASC, total_units_sold DESC;
#Resellable vs. Dead-Loss Inventory Recovery Rate
SELECT 
    ri.condition_received,
    COUNT(ri.return_item_id) AS total_line_items,
    SUM(ri.quantity) AS total_units,
    SUM(ri.quantity * oi.unit_price) AS estimated_loss_value
FROM return_items ri
JOIN order_items oi ON ri.order_item_id = oi.order_item_id
JOIN returns r ON ri.return_id = r.return_id
WHERE r.refund_status = 'processed'
GROUP BY ri.condition_received;
