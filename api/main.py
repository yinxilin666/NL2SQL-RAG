from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import health, query, reindex, rules, schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="NL2SQL RAG API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(query.router)
app.include_router(schema.router)
app.include_router(reindex.router)
app.include_router(rules.router)


@app.get("/")
async def root():
    return {"service": "NL2SQL RAG API", "docs": "/docs"}
