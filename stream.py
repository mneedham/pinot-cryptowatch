import cryptowatch as cw
import json
import datetime
import os

from google.protobuf.json_format import MessageToJson
from confluent_kafka import Producer

def acked(err, msg):
    if err is not None:
        print("Failed to deliver message: {0}: {1}"
              .format(msg.value(), err.str()))

def json_serializer(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise "Type %s not serializable" % type(obj)

producer = Producer({'bootstrap.servers': 'localhost:9092'})

# Set your API Key
cw.api_key = os.environ.get("KEY")

# Subscribe to resources (https://docs.cryptowat.ch/websocket-api/data-subscriptions#resources)
cw.stream.subscriptions = ["markets:*:trades"]
# cw.stream.subscriptions = ["instruments:232:trades"]

# What to do on each trade update
replace_keys = {
    "timestamp": "ts", "priceStr": "price", "amountStr": "amount",
    "timestampNano": "tsNano"
}


def handle_trades_update(trade_update):
    """
        trade_update follows Cryptowatch protocol buffer format:
        https://github.com/cryptowatch/proto/blob/master/public/markets/market.proto
    """
    global events_processed

    message = MessageToJson(trade_update)
    market_update = json.loads(message)["marketUpdate"]

    trades = market_update["tradesUpdate"]["trades"]
    market = market_update["market"]
    
    for trade in trades:
        message = {**trade, **market}
        for old, new in replace_keys.items():
          message[new] = message.pop(old)
        # print(message)
        payload = json.dumps(message, default=json_serializer, ensure_ascii=False).encode('utf-8')
        producer.produce(topic='trades', key=str(message["currencyPairId"]), value=payload, callback=acked)

        events_processed += 1
        if events_processed % 1000 == 0:
            print(f"{str(datetime.datetime.now())} Flushing after {events_processed} events")
            producer.flush()

events_processed = 0
cw.stream.on_trades_update = handle_trades_update


# Start receiving
cw.stream.connect()

# Call disconnect to close the stream connection
# cw.stream.disconnect()
