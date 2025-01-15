
from PIL import Image
from generator import Generator
from typing import Union
from fastapi.responses import StreamingResponse
from io import BytesIO
import os
import numpy as np

TO_ENGINE_SCALE = 20

class Chunk(object):

    def __init__(self, 
                 generator : Generator, 
                 coord : Union[np.array, tuple[int,int]], 
                 size : int, 
                 xz_scale : float, 
                 y_scale : float, 
                 buffer_size : int = 1, 
                 coord_size : int = 1,
                 skip : int = 1):

        # TODO: make this not shite
        self.chunk_size = size
        self.mesh_size = int(size // (skip / coord_size))
        self.real_chunk_size = self.chunk_size * self.xz_scale
        self.real_mesh_size

        self.buffer_size = buffer_size
        self.skip = int(skip)
        self.xz_scale = xz_scale
        self.y_scale = y_scale
        self.coord_size = int(coord_size)
        self.coord = np.array(coord)
     

        
        root_coord = ((self.coord * self.mesh_size) - self.skip) / self.xz_scale
        upper_corner_coord = (((self.coord + np.array([1, 1])) * self.mesh_size) + self.skip) / self.xz_scale

        self.heightmap_with_buffer = generator.make_heightmap(root_coord, upper_corner_coord, self.mesh_size + 2*self.buffer_size)
        self.texture_with_buffer = generator.make_texture(self.heightmap_with_buffer)

        self.heightmap = self.heightmap_with_buffer[self.buffer_size : (self.mesh_size + self.buffer_size), self.buffer_size : (self.mesh_size + self.buffer_size)]
        self.texture = self.texture_with_buffer[self.buffer_size : (self.mesh_size + self.buffer_size), self.buffer_size : (self.mesh_size + self.buffer_size), :]
        
        self.coord = (int(self.coord[0]), int(self.coord[1]))

    def make_model(self):
        # make vertices, edges and normals of mesh for heightmap
        # scale by y_scale
        pass

    def package_chunk(self):
        output = {}
        output['coord'] = [int(self.coord[0]), int(self.coord[1])]

        texture_image = Image.fromarray(self.texture, mode='RGB')
        texture_bytes_array = BytesIO()
        texture_image.save(texture_bytes_array, format="PNG")
        texture_bytes_array.seek(0)
        output['heightmap'] = 'yo'#StreamingResponse(heightmap_bytes_array)#, media_type='image/png')
        output['texture'] = StreamingResponse(texture_bytes_array, media_type='image/png')
        return output
    

    def get_heightmap(self):
        heightmap_bytes_array = BytesIO(self.heightmap.tobytes())
        return StreamingResponse(heightmap_bytes_array, media_type='application/octet-stream')

    def get_texture_response(self):
        texture_image = Image.fromarray(self.texture, mode='RGB')
        texture_bytes_array = BytesIO()
        texture_image.save(texture_bytes_array, format="PNG")
        texture_bytes_array.seek(0)
        return StreamingResponse(texture_bytes_array, media_type='image/png')



