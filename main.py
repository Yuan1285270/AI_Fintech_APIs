from fastapi import FastAPI
from routers import chat
from routers import predict, record

app = FastAPI()
app.include_router(predict.router)
app.include_router(chat.router)
