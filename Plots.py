
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 10, 'figure.autolayout': True})

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'retail_system'
}

try:
    conn = mysql.connector.connect(**db_config)
    print("Connected to retail_system database successfully.")
except mysql.connector.Error as err:
    print(f"Error connecting to database: {err}")
    exit()

query_revenue = """
SELECT 
    DATE_FORMAT(o.order_date, '%Y-%m') AS month,
    SUM(oi.quantity * oi.unit_price) AS gross_revenue,
    SUM(oi.quantity * oi.unit_price) - COALESCE(SUM(ri.quantity * oi.unit_price), 0) AS net_revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
LEFT JOIN return_items ri ON oi.order_item_id = ri.order_item_id
LEFT JOIN returns r ON ri.return_id = r.return_id AND r.refund_status = 'processed'
WHERE o.status != 'cancelled'
GROUP BY month
ORDER BY month;
"""

query_returns = """
SELECT 
    ri.reason,
    COUNT(ri.return_item_id) AS total_items,
    SUM(ri.quantity * oi.unit_price) AS lost_revenue
FROM return_items ri
JOIN order_items oi ON ri.order_item_id = oi.order_item_id
GROUP BY ri.reason
ORDER BY lost_revenue DESC;
"""

query_products = """
SELECT 
    p.product_name,
    p.stock_quantity,
    SUM(oi.quantity * oi.unit_price) - COALESCE(SUM(ri.quantity * oi.unit_price), 0) AS net_revenue
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
LEFT JOIN return_items ri ON oi.order_item_id = ri.order_item_id
GROUP BY p.product_id, p.product_name, p.stock_quantity
ORDER BY net_revenue DESC
LIMIT 10;
"""

df_revenue = pd.read_sql(query_revenue, conn)
df_returns = pd.read_sql(query_returns, conn)
df_products = pd.read_sql(query_products, conn)

conn.close()

fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('E-Commerce Business Performance Dashboard', fontsize=16, fontweight='bold')

if not df_revenue.empty:
    axes[0, 0].plot(df_revenue['month'], df_revenue['gross_revenue'], marker='o', label='Gross Revenue', color='#2b5c8f')
    axes[0, 0].plot(df_revenue['month'], df_revenue['net_revenue'], marker='s', label='Net Revenue', color='#2ca02c')
    axes[0, 0].set_title('Monthly Revenue Trend: Gross vs. Net', fontweight='bold')
    axes[0, 0].set_ylabel('Revenue ($)')
    axes[0, 0].legend()
    axes[0, 0].tick_params(axis='x', rotation=45)

if not df_returns.empty:
    sns.barplot(data=df_returns, x='lost_revenue', y='reason', ax=axes[0, 1], palette='Blues_r')
    axes[0, 1].set_title('Revenue Lost by Return Reason', fontweight='bold')
    axes[0, 1].set_xlabel('Lost Revenue ($)')
    axes[0, 1].set_ylabel('Return Reason')

if not df_products.empty:
    sns.barplot(data=df_products, x='net_revenue', y='product_name', ax=axes[1, 0], palette='Greens_r')
    axes[1, 0].set_title('Top 10 Products by Net Revenue', fontweight='bold')
    axes[1, 0].set_xlabel('Net Revenue ($)')
    axes[1, 0].set_ylabel('Product Name')

if not df_products.empty:
    sns.scatterplot(data=df_products, x='stock_quantity', y='net_revenue', size='net_revenue', sizes=(50, 400), ax=axes[1, 1], color='#e377c2')
    axes[1, 1].set_title('Top Sellers: Stock On-Hand vs Net Revenue', fontweight='bold')
    axes[1, 1].set_xlabel('Current Stock Quantity')
    axes[1, 1].set_ylabel('Net Revenue ($)')

plt.tight_layout()
plt.show()

print("=" * 60)
print("             BUSINESS GROWTH OBSERVATIONS & STRATEGY          ")
print("=" * 60)

if not df_revenue.empty:
    total_gross = df_revenue['gross_revenue'].sum()
    total_net = df_revenue['net_revenue'].sum()
    leakage_pct = ((total_gross - total_net) / total_gross) * 100 if total_gross > 0 else 0
    print(f"\n1. REVENUE LEAKAGE:")
    print(f"   - Total Gross Revenue: ${total_gross:,.2f}")
    print(f"   - Total Net Revenue:   ${total_net:,.2f}")
    print(f"   - Overall Revenue Leakage Rate: {leakage_pct:.2f}%")
    if leakage_pct > 15:
        print("   -> INSIGHT: High return leakage! Prioritize fixing sizing charts or product quality control.")

if not df_returns.empty:
    top_reason = df_returns.iloc[0]['reason']
    top_loss = df_returns.iloc[0]['lost_revenue']
    print(f"\n2. PRIMARY DRIVER OF RETURNS:")
    print(f"   - Main reason: '{top_reason}' account for ${top_loss:,.2f} in refunds.")
    if top_reason == 'defective':
        print("   -> ACTION: Review vendor quality standards immediately to minimize damaged shipments.")
    elif top_reason == 'wrong_size':
        print("   -> ACTION: Implement interactive size recommendation guides on product pages.")

if not df_products.empty:
    low_stock_winners = df_products[df_products['stock_quantity'] < 20]
    print(f"\n3. INVENTORY & FULFILLMENT RISK:")
    if not low_stock_winners.empty:
        print(f"   - CRITICAL: {len(low_stock_winners)} top-performing products have dangerously low stock (< 20 units).")
        print(f"   - Products at risk: {', '.join(low_stock_winners['product_name'].tolist())}")
        print("   -> ACTION: Reorder stock immediately to prevent revenue loss from stockouts.")
    else:
        print("   - Top-performing products currently have healthy stock buffer levels.")

print("\n" + "=" * 60)
