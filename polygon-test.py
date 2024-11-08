import websocket
from utils.configUtils import read_config


def on_message(ws, message):
    print(message)


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    ws.send('{"type":"subscribe","symbol":"NIO"}')
    # ws.send('{"type":"subscribe","symbol":"NIO241108P00008000"}')


if __name__ == "__main__":
    token = read_config('FINNHUB_API_TOKEN')
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={token}",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()
