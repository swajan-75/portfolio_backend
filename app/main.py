from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.chat import router as chat_router

app = FastAPI(title="Swajan Portfolio AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://swajan.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/v1/chat", tags=["AI"])

@app.get("/")
def read_root():
    return {"status": "Portfolio AI Backend is running"}
