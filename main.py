from fastapi import FastAPI

app = FastAPI()
@app.get("/")
async def root():
    return {"Hello":"야f호3"}