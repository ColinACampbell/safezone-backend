import json
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
import typing
from app.core.dependencies import get_db, get_user_from_token
import app.core.env as config_module
from app.database.models.group import Confidant, GeoRestriction, Group
import app.utils.user_utils as user_utils
from app.database.models.user import User, UserLocation
from app.routes import user_route
from app.routes import group_route
from app.routes import medical_record
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import math


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
app.include_router(router=medical_record.router, prefix="/medical-records")


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


    def getDistanceFromLatLonInM(self, lat1, lon1, lat2, lon2): # in meters

        R = 6371; # Radius of the earth in km
        dLat = math.radians(lat2 - lat1); 
        dLon = math.radians(lon2 - lon1);
        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2);
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
        d = R * c * 1000; # Distance in meters
        return d;


    async def update_user_location(self,group_id:int,message:str, geo_restrictions: list[GeoRestriction]) :

        if group_id not in self.groupMembersLocations :
            self.groupMembersLocations[group_id] = []

        date : datetime = datetime.now(timezone.utc)
        current_hour = date.hour

        if is_json(message) :
                user_data:typing.Dict[str,str] = json.loads(message) # convert string to json
                new_user_location: UserLocation = UserLocation(user_name=user_data["name"],user_id=int(user_data['id']), lat=user_data['lat'], lon=user_data['lon'])

                for restriction in geo_restrictions :

                    if current_hour >= restriction.from_time and current_hour <= restriction.to_time :
                        

                        user_distance_from_geo_restriction_point = self.getDistanceFromLatLonInM(lat1 = restriction.latitude, 
                                                                                                 lon1 = restriction.longitude, 
                                                                                                 lat2= new_user_location.lat, 
                                                                                                 lon2 = new_user_location.lon)
                        
                        if (user_distance_from_geo_restriction_point >= restriction.radius) :
                            logging.debug("Restriction violation spotted")
                            logging.debug(restriction.latitude)
                            logging.debug(restriction.longitude)
                            new_user_location.geo_flag = True
                            new_user_location.geo_radius = user_distance_from_geo_restriction_point - restriction.radius
                        
                        logging.debug(user_distance_from_geo_restriction_point)

                # find the old user location then, update it
                existing_location = None
                for existing_user_location_item in self.groupMembersLocations[group_id] :
                    if existing_user_location_item.user_id == new_user_location.user_id :
                        existing_location = existing_user_location_item
                
                # finally update the location
                if existing_location != None :
                    self.groupMembersLocations[group_id].remove(existing_location)
                    self.groupMembersLocations[group_id].append(new_user_location)
                else :
                    self.groupMembersLocations[group_id].append(new_user_location)


                


    async def send_message(self,group_id:int) :
        if group_id not in self.groupMembersLocations :
            self.groupMembersLocations[group_id] = []

        if group_id in self.sockets :
            # get all the listeners
            listeners = self.sockets[group_id]
            # send the update to all the listners
            for listener in listeners :
                #if listener != user_socket :
                await listener.send_text(json.dumps([x.to_json() for x in self.groupMembersLocations[group_id]]))

connectionsManager = ConnectionManager()


@app.websocket("/user/location-update/{user_id}")
async def user_location_update(websocket:WebSocket, user_id:int, db:Session=Depends(get_db)) :
    # connect user
    # get the user groups
    # update the location of the user in all their groups
    await websocket.accept()

    #user = get_user_from_token(db,user_token)
    logging.debug("User autheticated")

    groups:list[Group] = db.query(Group).join(Confidant,Confidant.group == Group.id).join(User,user_id == Confidant.user).filter(User.id == user_id).all()
    logging.debug("Fetched groups")

    try :
        while True :
            data = await websocket.receive_text()
            for group in groups :
                await connectionsManager.update_user_location(group.id,data)
                logging.debug(group.id in connectionsManager.groupMembersLocations)

            await websocket.send_text("")
    except WebSocketDisconnect :
        logging.debug('Connect closed')    
    

@app.websocket("/group/{group_id}")
async def group_socket(websocket:WebSocket,group_id:int,) :
    await connectionsManager.add_connection(websocket,group_id)
    logging.debug("Accepted request")

    try :
        while True :
            data = await websocket.receive_text()
            logging.debug("Member location changed")
            await connectionsManager.send_message(group_id)
    except WebSocketDisconnect :
        logging.debug('Connect closed')
        await connectionsManager.disconnect(websocket,group_id)
        #await websocket.send_text(data)


@app.websocket("/stream-group-locations/{user_token}")
async def location_update_socket(websocket:WebSocket,user_token:str, db: Session = Depends(get_db)) :


    await websocket.accept()

    user = get_user_from_token(db,user_token)
    logging.debug("User autheticated")

    groups: list[Group] = db.query(Group).join(Confidant,Confidant.group == Group.id).join(User,User.id == Confidant.user).filter(User.id == user.id).all()
    logging.debug("Fetched groups")

    geo_restrictions = db.query(GeoRestriction).filter(GeoRestriction.user == user.id);

    try :
        while True :

            data = await websocket.receive_text()

            for group in groups :

                await connectionsManager.update_user_location(group.id,data,geo_restrictions) # update the user location for all the groups they are in
                logging.debug("Updated {}'s location".format(user.email))

            await websocket.send_text("")
    except WebSocketDisconnect as error:
        logging.debug("User {} disconnected from the group stream".format(user.email))
        logging.debug("Error is {}".format(error))


@app.websocket("/get-group-locations/{user_token}")
async def group_listen_socket(websocket:WebSocket,user_token:str, db: Session = Depends(get_db)) :

    await websocket.accept()

    user = get_user_from_token(db,user_token)
    logging.debug("User autheticated")

    groups: list[Group] = db.query(Group).join(Confidant,Confidant.group == Group.id).join(User,User.id == Confidant.user).filter(User.id == user.id).all()
    logging.debug("Fetched groups")

    try :

        while True :
            data = await websocket.receive_text()
            members_locations : list[UserLocation] = []
            for group in groups :
                if group.id in list(connectionsManager.groupMembersLocations.keys()):
                        members_locations = connectionsManager.groupMembersLocations[group.id] + members_locations

            logging.debug("User {} requested updates for all locations".format(user.email))
            logging.debug(json.dumps([x.to_json() for x in members_locations]))
            await websocket.send_text(json.dumps([x.to_json() for x in members_locations]))
    except WebSocketDisconnect :
        logging.debug("User {} disconnected from the group listen stream".format(user.email))