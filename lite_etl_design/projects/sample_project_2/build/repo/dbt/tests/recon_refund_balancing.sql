{{ config(tags=['recon'], enabled=false) }}
-- R3 (requirements/05 check 3): every refund links to an order; SUM(refunds) per
-- customer/period within tolerance. NOT in the walking-skeleton slice (no refunds
-- in it) - disabled until fct_refund is implemented. Do not tag 'slice'.
select 1 as _todo where false
