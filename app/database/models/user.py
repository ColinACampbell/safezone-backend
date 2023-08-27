import json
from app.database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

class User(Base) :
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    password = Column(String)

class UserLocation:
    def __init__(self, user_id: int,user_name:str,lat:str, lon:str) -> None:
        self.lon = lon;
        self.lat = lat;
        self.user_id = user_id;  
        self.user_name = user_name; # user's name,  not user name as in alias
        self.geo_flag = False
        self.geo_radius = float(0)

    def to_json(self) :        
        return json.dumps({"lat":self.lat,"lon":self.lon,"id":self.user_id, "name":self.user_name, "geo_fence_distance":self.geo_radius, "geo_flag":self.geo_flag})
    
    def __str__(self) -> str:
        return self.to_json();

