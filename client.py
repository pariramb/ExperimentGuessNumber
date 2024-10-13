import asyncio
import websockets
import json

class Player:
    def __init__(self):
        self.name = ""
        self.answers = list()

async def async_input(prompt = ''):
    return await asyncio.to_thread(input, prompt)

player = Player()

async def websocket_handler(uri, send_queue):
    async with websockets.connect(uri) as websocket:
        send_task = asyncio.create_task(send_messages(websocket, send_queue))
        receive_task = asyncio.create_task(receive_messages(websocket, send_queue))
        done, pending = await asyncio.wait(
            [send_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

async def send_messages(websocket, send_queue):
    while True:
        message = await send_queue.get()
        await websocket.send(message)
        print(f"Отправлено сообщение на сервер: {message}")

async def receive_messages(websocket, send_queue):
    async for message in websocket:
        print(f"Получено сообщение от сервера: {message}")
        data = json.loads(message)
        if data['action'] == 'success':
            print("Успешно отправлено")
            continue
        elif data['action'] == 'start':
            print("Число загадано, либо изменено")
        elif data['action'] == 'result':
            if data['result'] == '==':
                print("Вы угадали число!!!")
            elif data['result'] == '>':
                print("Ваше число больше")
            elif data['result'] == '<':
                print("Ваше число меньше")
        await send_queue.put(json.dumps({
                        "action": "success",
                    }))

async def input_handler(send_queue):
    player.name = await async_input("Введите имя\n")
    data = { 
        "action": "connect",
        "name": player.name
    }
    message = json.dumps(data)
    await send_queue.put(message)
    print("Доступные действия:")
    print("1. Отправить число")
    print("2. История ответов")
    while True:
        user_input = await async_input("Введите номер действия:\n")
        if user_input == "1":
            number = await async_input("Введите число\n")
            player.answers.append(number)
            data = {
                "action": "guess",
                "number": number
            }
            message = json.dumps(data)
            await send_queue.put(message)
        elif user_input == "2":
            print(f"Прошлые ответы: {player.answers}")

async def main():
    # uri = await async_input("Введите адрес сервера\n")
    uri = "ws://localhost:8765"
    send_queue = asyncio.Queue()
    websocket_task = asyncio.create_task(websocket_handler(uri, send_queue))
    input_task = asyncio.create_task(input_handler(send_queue))
    done, pending = await asyncio.wait(
        [websocket_task, input_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

if __name__ == '__main__':
    asyncio.run(main())