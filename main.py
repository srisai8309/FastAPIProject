from fastapi import FastAPI
from database import Base, engine
from routers.student import router
from routers.auth_router import router as auth_router
app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(router)
app.include_router(auth_router)
@app.get("/")
def home():
    return {"message": "Welcome"}