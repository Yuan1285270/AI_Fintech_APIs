from fastapi import FastAPI
from routers import chat
from routers import predict, record
from routers import analyze

app = FastAPI()
app.include_router(predict.router)
app.include_router(chat.router)
app.include_router(analyze.router)
