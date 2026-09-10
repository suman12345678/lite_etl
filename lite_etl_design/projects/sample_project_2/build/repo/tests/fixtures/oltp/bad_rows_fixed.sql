-- The `bad` dataset after a data correction: order 1005's amount is fixed to +42.00
-- (and its line to +42.00). Re-running `make demo DATASET=fixed` shows 0 quarantined
-- rows and reconciliation PASS - the "data correction" half of the story.

create table if not exists customers(
  customer_id int, email varchar, country varchar, updated_at timestamp, is_deleted boolean);
insert into customers values
  (1,'ada@example.test','GB','2026-09-08 10:00:00',false),
  (2,'bo@example.test' ,'US','2026-09-08 11:00:00',false),
  (3,'cy@example.test' ,'CA','2026-09-08 09:30:00',false),
  (4,'gone@example.test','GB','2026-09-07 08:00:00',true);

create table if not exists products(
  product_id int, category varchar, price decimal(12,2), updated_at timestamp);
insert into products values
  (10,'Shoes' ,24.00,'2026-09-01 09:00:00'),
  (11,'Socks' ,15.00,'2026-09-01 09:00:00'),
  (12,'Bag'   ,120.00,'2026-09-01 09:00:00'),
  (13,'Jacket',34.00,'2026-09-01 09:00:00');

create table if not exists orders(
  order_id int, customer_id int, currency varchar, net_amount decimal(12,2),
  is_return boolean, order_date date, updated_at timestamp, is_deleted boolean);
insert into orders values
  (1001,1,'GBP', 39.00,false,'2026-09-08','2026-09-08 12:00:00',false),
  (1002,2,'USD',120.00,false,'2026-09-08','2026-09-08 12:05:00',false),
  (1003,3,'CAD', 68.00,false,'2026-09-08','2026-09-08 12:10:00',false),
  (1004,1,'GBP',-15.60,true ,'2026-09-08','2026-09-08 15:00:00',false),
  (1005,2,'USD', 42.00,false,'2026-09-08','2026-09-08 16:45:00',false);  -- corrected

create table if not exists order_lines(
  order_id int, line_no int, product_id int, quantity int, net_amount decimal(12,2));
insert into order_lines values
  (1001,1,10,1,24.00),
  (1001,2,11,1,15.00),
  (1002,1,12,1,120.00),
  (1003,1,13,2,68.00),
  (1004,1,11,1,-15.60),
  (1005,1,12,1,42.00);
