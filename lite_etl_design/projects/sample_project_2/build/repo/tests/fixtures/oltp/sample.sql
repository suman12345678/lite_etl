-- tiny synthetic OLTP snapshot (no PII). Loaded as bronze.oltp__* for --target ci.
create table if not exists customers(customer_id int, email varchar, country varchar, updated_at timestamp, is_deleted boolean);
insert into customers values (1,'a@example.test','GB','2026-09-08 10:00',false),(2,'b@example.test','US','2026-09-08 11:00',false);
create table if not exists products(product_id int, category varchar, price decimal(12,2), updated_at timestamp);
insert into products values (10,'Shoes',49.99,'2026-09-01 09:00');
create table if not exists orders(order_id int, customer_id int, currency varchar, net_amount decimal(12,2), order_date date, updated_at timestamp, is_deleted boolean);
insert into orders values (1001,1,'GBP',49.99,'2026-09-08','2026-09-08 12:00',false);
create table if not exists order_lines(order_id int, line_no int, product_id int, quantity int, net_amount decimal(12,2));
insert into order_lines values (1001,1,10,1,49.99);
