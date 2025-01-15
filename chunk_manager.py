
from PIL import Image
import os
import asyncio
import numpy as np
from numpy.random import rand
from chunk import Chunk
from generator import Generator
#from multiprocessing import Process
from threading import Thread, Event, active_count
from multiprocessing import Queue

TO_ENGINE_SCALE = 20
MAX_CHUNK_WIDTH = 100

class ChunkManager:

    def __init__(self, chunk_size=100, n_chunks_radius = 5, xz_scale = 1, y_scale=150):

        self.chunk_size = chunk_size
        self.chunk_mesh_size = chunk_size + 1
        self.n_chunks_radius = n_chunks_radius
        self.n_chunks_width = (self.n_chunks_radius * 2) + 1
        self.xz_scale = xz_scale
        self.y_scale = y_scale
        self.noise_seed = int(1000000 * rand())
        self.chunks: dict[tuple[int,int],Chunk] = {}
        self.terrain_generator = Generator(seed=self.noise_seed)
        self.center_chunk = (0, 0)        

    @staticmethod
    def package_chunks(generated_chunks, coords_to_delete):
        response = {'to_generate' : {}, 'to_delete' : []}

        for chunk in generated_chunks:
            chunk_id = ChunkManager.coord_to_id(chunk.coord)
            response['to_generate'][chunk_id] = chunk.package_chunk()

        for coord in coords_to_delete:
            response['to_delete'].append(ChunkManager.coord_to_id(coord))
        return response

    @staticmethod
    def coord_to_id(coord):
        return f"chunk_{coord[0]}_{coord[1]}"

    def coord_to_texture_file_coord(self, coord):
        return (coord[0] % self.n_chunks_width, coord[1] % self.n_chunks_width)


    def get_texture(self, coord):
        return self.chunks[coord].get_texture_response()

    def get_heightmap(self, coord):
        return self.chunks[coord].get_heightmap()
    
    @staticmethod
    async def initialize_terrain_chunk(generator : Generator, 
                                       coord : tuple[int, int], 
                                       chunk_mesh_size : int, 
                                       xz_scale, 
                                       y_scale, 
                                       coord_size,
                                       skip):
        terrain_chunk = Chunk(generator,
                                     coord, 
                                     chunk_mesh_size,
                                     xz_scale=xz_scale,
                                     y_scale=y_scale,
                                     coord_size=coord_size,
                                     skip=skip
                                     )
        return terrain_chunk


    async def async_generate_chunks(self, coords_to_generate : list, skip_values : list):
        tasks = []
        for i in range(len(coords_to_generate)):
            coord = coords_to_generate[i]
            skip = skip_values[i]

            tasks.append(ChunkManager.initialize_terrain_chunk(
                            self.terrain_generator, 
                            coord, 
                            self.chunk_mesh_size, 
                            self.xz_scale,
                            self.y_scale,
                            skip, # coord_size = skip  
                            skip))
        print("Doing async chunk initialization")
        terrain_chunks = await asyncio.gather(*tasks)
        return terrain_chunks

    def bounds_to_skip(self, bounds):
        width = bounds[1][0] - bounds[0][0]
        return 1 + int(width)

    def get_all_chunk_coords_in_bounds(self, bounds):
        coords = []
        bottom_left_coord = (int(np.floor(bounds[0][0] / self.skip)), int(np.floor(bounds[0][1] / self.skip)))
        top_right_coord = (int(np.floor(bounds[1][0] / self.skip)), int(np.floor(bounds[1][1] / self.skip)))
        for i in range(bottom_left_coord[0], top_right_coord[0]+1):
            for j in range(bottom_left_coord[1], top_right_coord[1]+1):
                coords.append((i,j))
        return coords

    def generate(self, bounds: list[tuple[float, float]]):

        skip = self.bounds_to_skip(bounds)
        if skip != self.skip:
            self.skip = skip
            chunk_coords_to_delete = [coord for coord in self.chunks]
            chunk_coords_to_generate = self.get_all_chunk_coords_in_bounds(bounds)

        else:

            coords_in_bounds = set(self.get_all_chunk_coords_in_bounds(bounds))
            existing_chunk_coords = set(self.chunks.keys())

            chunk_coords_to_generate = list(coords_in_bounds.difference(existing_chunk_coords))
            chunk_coords_to_delete = list(existing_chunk_coords.difference(coords_in_bounds))

        print("to generate:")
        print(chunk_coords_to_generate)
        print("to delete:")
        print(chunk_coords_to_delete)

        skip_values = [self.skip for i in range(len(chunk_coords_to_generate))]
        terrain_chunks = asyncio.run(self.async_generate_chunks(chunk_coords_to_generate, skip_values))

        for coord in chunk_coords_to_delete:
            self.chunks.pop(coord)

        for terrain_chunk in terrain_chunks:
            self.chunks[terrain_chunk.coord] = terrain_chunk
        
        return chunk_coords_to_generate, chunk_coords_to_delete

    def get_coords_only_from_prev_generation(self, center_coord, prev_center_coord):
        coords = set()
        prev_coords = set()
        for i in range(-self.n_chunks_radius, self.n_chunks_radius + 1):
            for j in range(-self.n_chunks_radius, self.n_chunks_radius + 1):
                coords.add((center_coord[0] + i, center_coord[1] + j))
                prev_coords.add((prev_center_coord[0] + i, prev_center_coord[1] + j))
        
        not_shared = prev_coords.difference(coords)
        prev_only = prev_coords.intersection(not_shared)
        prev_only_in_chunks = prev_only.intersection(set(self.chunks.keys()))
        return list(prev_only_in_chunks)
       
    def get_any_outer_chunks(self, center_coord):
        coords = set()
        for i in range(-self.n_chunks_radius, self.n_chunks_radius + 1):
            for j in range(-self.n_chunks_radius, self.n_chunks_radius + 1):
                coords.add((center_coord[0] + i, center_coord[1] + j))
        
        current_chunks = set(self.chunks.keys())
        return current_chunks.difference(coords)
