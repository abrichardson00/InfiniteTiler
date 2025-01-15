import numpy as np
import vnoise

class Generator():

    def __init__(self, seed):
        self.seed = seed
        self.noise = vnoise.Noise(self.seed)

    def make_heightmap(self, corner_1, corner_2, n_coords) -> np.array:

        p_noise = self.noise.noise2(0.01*np.linspace(corner_1[0], corner_2[0], num=n_coords, endpoint=True), 
                                    0.01*np.linspace(corner_1[1], corner_2[1], num=n_coords, endpoint=True),
                                    grid_mode=True)

        heightmap = (p_noise * 100).astype(np.uint16)
        return heightmap

    
    def make_texture(self, heightmap):
        max_height = heightmap.max()
        print(heightmap.shape)
        heightmap_normalized = heightmap[1:heightmap.shape[0]-1, 1:heightmap.shape[1]-1]#.astype(np.float32) * (1.0 / max_height)

        size = heightmap_normalized.shape[0]

        texture = np.zeros((size, size, 3), dtype=np.uint8)
        texture[heightmap_normalized > 50, 0] = 255
        return texture.astype(np.uint8)