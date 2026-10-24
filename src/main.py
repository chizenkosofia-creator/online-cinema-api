from fastapi import FastAPI
from src.movies.router import router as movies_router
from src.accounts.router import router as accounts_router
app = FastAPI(title="Online Cinema API")

app.include_router(movies_router)
app.include_router(accounts_router)
