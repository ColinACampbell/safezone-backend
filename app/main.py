from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import typing
import app.core.env as config_module
from app.routes import user_route
from app.routes import group_route
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(encoding='utf-8', level=logging.DEBUG)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"]
)

app.include_router(router=user_route.router, prefix="/users")
app.include_router(router=group_route.router, prefix="/groups")

@app.get("/")
def get_stuff() :
    print(config_module.config)
    return {"message":"hello World"}

class ConnectionManager :
    def __init__(self) -> None:
        self.sockets: typing.Dict[str,list[WebSocket]] = {}

    async def disconnect(self,websocket:WebSocket, group_name:str):
        self.sockets[group_name].remove(websocket);
    
    async def add_connection(self,websocket:WebSocket, group_name:str)->WebSocket: 
        await websocket.accept()
        if group_name in self.sockets :
            self.sockets[group_name].append(websocket)
        else :
            self.sockets[group_name] = []
            self.sockets[group_name].append(websocket)

    async def send_message(self,group_name:str, user_socket:WebSocket, message:str) :
        logging.debug("Message sent is "+message)
        if group_name in self.sockets :
            listeners = self.sockets[group_name]
            
            for listener in listeners :
                #if listener != user_socket :
                await listener.send_text(message)

connectionsManager = ConnectionManager()

@app.websocket("/group/{group_name}")
async def group_socket(websocket:WebSocket,group_name:str,) :
    await connectionsManager.add_connection(websocket,group_name)
    #await websocket.accept();
    logging.debug("Accepted request")

    try :
        while True :
            data = await websocket.receive_text()
            await connectionsManager.send_message(group_name,websocket,data)
    except WebSocketDisconnect :
        logging.debug('Connect closed')
        await connectionsManager.disconnect(websocket,group_name)
        #await websocket.send_text(data)


