import os
from dotenv import dotenv_values

values = None
if os.environ.get("DEBUG") == None :
    values = dotenv_values(".env.dev")
else:
    values = os.environ

config = {
    **values
}