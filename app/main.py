from fastapi import FastAPI, WebSocket
import typing
import app.core.env as config_module
from app.database import Base

app = FastAPI()

@app.get("/")
def get_stuff() :
    print(config_module.config)
    return {"message":"hello World"}


class ConnectionManager :
    def __init__(self) -> None:
        self.sockets: typing.Dict[str,list[WebSocket]] = {}
    
    async def add_connection(self,websocket:WebSocket, group_name:str)->WebSocket: 
        await websocket.accept()
        if group_name in self.sockets :
            self.sockets[group_name].append(websocket)
        else :
            self.sockets[group_name] = []
            self.sockets[group_name].append(websocket)

    async def send_message(self,group_name:str, user_socket:WebSocket, message:str) :
        if group_name in self.sockets :
            listeners = self.sockets[group_name]
            for listener in listeners :
                if listener != user_socket :
                    await listener.send_text(message)
        else :
            return 

connectionsManager = ConnectionManager()

@app.websocket("/group/{group_name}")
async def group_socket(websocket:WebSocket,group_name:str,) :
    await connectionsManager.add_connection(websocket,group_name)
    while True :
        data = await websocket.receive_text()
        await connectionsManager.send_message(group_name,websocket,data)