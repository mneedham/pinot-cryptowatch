#!/bin/bash

curl  https://api.cryptowat.ch/pairs 2>/dev/null  | 
jq -c '.result[] | {id: .id, base: .base.id, baseSymbol: .base.symbol, baseName: .base.name, quote: .quote.id, quoteSymbol: .quote.symbol, quoteName: .quote.name}' > pairs.json

curl  https://api.cryptowat.ch/exchanges 2>/dev/null | jq -c '.result[]' > exchanges.json
curl  https://api.cryptowat.ch/markets 2>/dev/null | jq -c '.result[]' > markets.json

