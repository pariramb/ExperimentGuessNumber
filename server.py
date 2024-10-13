import asyncio
import websockets
import json

async def send_message_to_client(websocket, message):
    if websocket:
        try:
            await websocket.send(message)
            print(f"Сообщение отправлено клиенту: {message}")
        except websockets.exceptions.ConnectionClosed:
            print(f"Соединение с клиентом закрыто")
    else:
        print(f"Клиент не найден")

async def async_input(prompt = ''):
    return await asyncio.to_thread(input, prompt)

class Moves:
    numbers = list()
    player: str


class Server:
    def __init__(self):
        self.name_by_websocket = {}
        self.websoket_by_name = {}
        self.waiting_for_answer = dict()
        self.current_player = ""
        self.correct_number: int = 1
        # self.move_regex = re.compile(r'^[1-3],[1-3]$')

server = Server()

async def handle_client(websocket):
    async for message in websocket:
        global server
        data = json.loads(message)

        if data['action'] == 'connect' and data['name'] not in server.websoket_by_name.keys():
            print("Новый игрок")
            server.websoket_by_name[data['name']] = websocket
            server.name_by_websocket[websocket] = data['name']
            await websocket.send(json.dumps({"action": "success"}))
        
        elif data['action'] == 'guess':
            server.waiting_for_answer[server.name_by_websocket[websocket]] = int(data['number'])
            await websocket.send(json.dumps({"action": "success"}))

        elif data['action'] == 'success':
            print(f"Сообщение доставлено {server.name_by_websocket[websocket]}")


async def main_menu():
    print("Выберите действие:")
    print("1. Загадать число")
    print("2. Число загадано/загадано новое число")
    print("3. Ответить участнику")
    print("4. Список участников, ожидающих ответ")
    print("5. Таблица лидеров")
    print("6. Выйти")
    
    choice = await async_input("Введите номер действия:\n")

    return choice

async def interface():
    while True:
        choice = await main_menu()
        if choice == "1":
            await make_number()
        elif choice == "2":
            await send_info()
        elif choice == "3":
            await give_answer()
        elif choice == "4":
            print(f"{server.waiting_for_answer.keys()}")
        elif choice == "5":
            pass
        elif choice == "6":
            print("До свидания!")
            break
        else:
            print("Неверный выбор. Попробуйте еще раз.")


async def give_answer():
    print(f"{server.waiting_for_answer.keys()}")
    name = await async_input("Выберите имя из списка:\n")
    number = int(server.waiting_for_answer[name])
    websocket = server.websoket_by_name[name]
    if number == server.correct_number:
        await websocket.send(json.dumps({"action": "result",
                                   "result": "=="}))
    elif number > server.correct_number:
        await websocket.send(json.dumps({"action": "result",
                                    "result": ">"}))
    elif number < server.correct_number:
        await websocket.send(json.dumps({"action": "result",
                                    "result": "<"}))


async def send_info():
    for websocket in server.name_by_websocket.keys():
        await send_message_to_client(websocket, json.dumps({"action": "start"}))

async def make_number():
    server.correct_number = int(await async_input("Введите число\n"))

async def start_server():
    server = await websockets.serve(handle_client, "localhost", 8765)
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        print("Сервер остановлен")
        server.close()
        await server.wait_closed()

async def main():
    server_task = asyncio.create_task(start_server())
    interface_task = asyncio.create_task(interface())
    await asyncio.wait([server_task, interface_task], return_when=asyncio.FIRST_COMPLETED)
    if not server_task.done():
        server_task.cancel()
        await server_task

if __name__ == "__main__":
    asyncio.run(main())