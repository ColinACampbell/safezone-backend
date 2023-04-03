import json
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
import typing
from app.core.dependencies import get_db, get_user_from_token
import app.core.env as config_module
from app.database.models.group import Confidant, Group
import app.utils.user_utils as user_utils
from app.database.models.user import User, UserLocation
from app.routes import user_route
from app.routes import group_route
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy.orm import Session


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

def is_json(myjson:str):
        try:
            json.loads(myjson)
        except ValueError as e:
            return False
        return True

class ConnectionManager :

    def is_json(myjson:str):
        try:
            json.loads(myjson)
        except ValueError as e:
            return False
        return True


    def __init__(self) -> None:
        self.sockets: typing.Dict[str,list[WebSocket]] = {}
        self.groupMembersLocations : typing.Dict[str,list[UserLocation]] = {}

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
        #logging.debug("Message sent is "+message)

        if group_name not in self.groupMembersLocations :
            self.groupMembersLocations[group_name] = []

        if group_name in self.sockets :

            # check if the message is a json object
            if is_json(message) :
                user_data:typing.Dict[str,str] = json.loads(message) # convert string to json
                new_user_location: UserLocation = UserLocation(user_name=user_data["name"],user_id=int(user_data['id']), lat=user_data['lat'], lon=user_data['lon'])

                # find the old user location then, update it
                existing_location = None
                for existing_user_location_item in self.groupMembersLocations[group_name] :
                    if existing_user_location_item.user_id == new_user_location.user_id :
                        existing_location = existing_user_location_item
                
                # finally update the location
                if existing_location != None :
                    self.groupMembersLocations[group_name].remove(existing_location)
                    self.groupMembersLocations[group_name].append(new_user_location)
                else :
                    self.groupMembersLocations[group_name].append(new_user_location)


                # get all the listeners
                listeners = self.sockets[group_name]
                
                # send the update to all the listners
                for listener in listeners :
                    #if listener != user_socket :
                    await listener.send_text(json.dumps([x.to_json() for x in self.groupMembersLocations[group_name]]))

connectionsManager = ConnectionManager()

@app.websocket("/group/{group_name}")
async def group_socket(websocket:WebSocket,group_name:str,) :
    await connectionsManager.add_connection(websocket,group_name)
    logging.debug("Accepted request")

    try :
        while True :
            data = await websocket.receive_text()
            logging.debug("Member location changed")
            await connectionsManager.send_message(group_name,websocket,data)
    except WebSocketDisconnect :
        logging.debug('Connect closed')
        await connectionsManager.disconnect(websocket,group_name)
        #await websocket.send_text(data)


@app.websocket("/stream-group-locations/{user_token}")
async def group_socket(websocket:WebSocket,user_token:str, db: Session = Depends(get_db)) :


    await websocket.accept()

    user = get_user_from_token(db,user_token)
    logging.debug("User autheticated")

    groups = db.query(Group).join(Confidant,Confidant.group == Group.id).join(User,User.id == Confidant.user).filter(User.id == user.id).all()
    logging.debug("Fetched groups")

    try :
        while True :

            dd = await websocket.receive_text()

            members_locations : list[UserLocation] = []
            for group in groups :
                if group.name in list(connectionsManager.groupMembersLocations.keys()):
                    members_locations = connectionsManager.groupMembersLocations[group.name] + members_locations

            logging.debug("User {} requested update".format(user.email))
            logging.debug(json.dumps([x.to_json() for x in members_locations]))
            await websocket.send_text(json.dumps([x.to_json() for x in members_locations]))
    except WebSocketDisconnect :
        print("User {} disconnected from the group stream".format(user.email))