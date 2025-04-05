from fastapi import FastAPI
from routers import predict, suggest, record

app = FastAPI()
app.include_router(predict.router)
