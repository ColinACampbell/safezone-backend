from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def get_stuff() :
    return {"message":"hello World"}