-- Highest trading currency pairs
select currencyPairId, orderSide, sum(amount) AS totalAmount
from trades 
group by currencyPairId, orderSide
order by totalAmount DESC


-- Bitcoin transactions
select avg(price) AS avgPrice, max(price) as maxPrice, min(price) AS minPrice, 
        count(*) AS count, sum(amount) AS amountTraded
from trades 
WHERE lookUp('pairs', 'baseName', 'id', currencyPairId) = 'Bitcoin'
AND lookUp('pairs', 'quoteName', 'id', currencyPairId) = 'United States Dollar'
AND tsMs > cast(ago('PT30M') as long)

select avg(price) AS avgPrice, max(price) as maxPrice, min(price) AS minPrice, 
        count(*) AS count, sum(amount) AS amountTraded
from trades 
WHERE IN_SUBQUERY(
  currencyPairId, 
  'SELECT ID_SET(id) FROM pairs WHERE baseName = ''Bitcoin'' AND quoteName = ''United States Dollar'''
  ) = 1
AND tsMs > cast(ago('PT30M') as long)



SELECT *
FROM trades 
WHERE IN_PARTITIONED_SUBQUERY(
  currencyPairId, 
  'SELECT ID_SET(id) FROM pairs WHERE baseName = ''Bitcoin'''
  ) = 1


select * from  trades
where IN_ID_SET(
  currencyPairId, 
  'AgAAAAABAAAAADowAAACAAAAAAArAAIANwEYAAAAcAAAAAkAEAAfACUAJgAyAEgASwBjAGcAbQB1AHgAggCGAIsAkQCqAK8AtQC2ANkA4wDnAOgA6gD2ABIBVgFwAUMCRAKCAlUFXwUUBnkGuQYnCL8J3hNsFKQUqRRic5mwrbDBsPOwKrHqsfCx8rH4sR2yQLJLskyyT7InsyizMLM1s02zTrNPs1CzUbNSs1OzVLNVs7Ozt7PEs8izybPNs9Gz17PYs9mz4LPis+Sz6rPzs/az97P4s/mz/rP/swi0CrQLtBG0ErQVtBa0IbQltC20PrRCtEW0RrRHtEi0S7QntWi1brV1tXa1d7V4tXq1g7WHtYq1i7WRtZK1k7WWtZ619rUHtg22FrYXthm2HLZJtly2YLZjtmu2bLZutm+2fraBtom2l7aatpu2nbaetqG2ubbAtsW2x7bMttG20rbZttu24rbqtlq3aLeZt5q3orept723BbgRuBm4KLgpuCy4NbiKuKW4rbjVuOS45bjvuAW5G7kquUK5VLlYuWO5brl1uXa5hLmIuZq5oLm0ub25xbnGuc6517niueO56rnxuQW6GrobuiC6JrosujG6Nbo2uj+6RbpGukq6T7pWumu6dbqZuqO6pLquurO6xLrNuuW6/LoHuw27DrsTuxq7J7szu0m7UrtZu2i7abtyu3q7n7uzu7q7v7vJu8q7zrvUu9e74Lvlu/K7DrwPvBW8OrxDvFu8brx7vI28kbyWvJe8nbygvKO8trzHvM681bzWvNm837znvPq8EL4YvjS+H78tv8q/ZMBowG7An8BHwUrBssS8xL/EwsTFxMjEy8TOxNTE+8QdxSHFU8VpxafFqcWuxbfFdcZ9xl7IbciByKDI+8gNyVHJzMkMzFTMwc7EzsjO387hznHPdc/wzwTQBdAG0AfQC9A40DnQZdC70F7RrNIM0xnTH9Ms02XTidOZ05rTn9MK1EnUStQ='
) = 1