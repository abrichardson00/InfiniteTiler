from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from chunk_manager import ChunkManager
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    #allow_origins=origins,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

chunk_manager = ChunkManager(chunk_size=100, n_chunks_radius=2)

#def package_chunks(chunks):

class CurrAndPrevCoord(BaseModel):
    x: int
    z: int
    prev_x: int | None = None
    prev_z: int | None = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/chunk_updates")
def get_chunk_updates(c: CurrAndPrevCoord):
    if c.prev_x is None or c.prev_z is None or (c.prev_x == c.x and c.prev_z == c.z):
        prev_coord = None
    else:
        prev_coord = (c.prev_x, c.prev_z)

    print(f"{(c.x, c.z)}, {prev_coord}")
    if prev_coord is not None:
        if abs(c.x - c.prev_x) + abs(c.z - c.prev_z) > 1:
            quit()
    coords_to_generate, coords_to_delete = chunk_manager.generate((c.x, c.z), prev_coord)
    response = {'to_generate' : coords_to_generate, 'to_delete' : coords_to_delete}
    return response

@app.get("/textures/{x}/{y}")
def get_texture(x: int, y: int):
    #print(f"{x}, {y}")
    return chunk_manager.get_texture((x, y))

@app.get("/heightmaps/{x}/{y}")
def get_texture(x: int, y: int):
    return chunk_manager.get_heightmap((x, y))