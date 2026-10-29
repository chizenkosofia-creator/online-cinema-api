import secrets
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from src.config.settings import settings

app = FastAPI(
    title="Online Cinema API",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/v1/openapi.json"
)

security = HTTPBasic()


def verify_docs_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    correct_username = secrets.compare_digest(credentials.username, settings.DOCS_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.DOCS_PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui(username: str = Depends(verify_docs_credentials)):
    return get_swagger_ui_html(openapi_url=app.openapi_url, title="Online Cinema API - Swagger UI")


@app.get("/redoc", include_in_schema=False)
async def custom_redoc(username: str = Depends(verify_docs_credentials)):
    return get_redoc_html(openapi_url=app.openapi_url, title="Online Cinema API - ReDoc")
