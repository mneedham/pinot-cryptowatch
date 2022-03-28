-- Highest trading currency pairs
select currencyPairId, orderSide, sum(amount) AS totalAmount
from trades 
group by currencyPairId, orderSide
order by totalAmount DESC