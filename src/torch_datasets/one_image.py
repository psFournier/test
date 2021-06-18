import numpy as np
import rasterio
from rasterio.windows import Window
from torch.utils.data import Dataset
from abc import ABC
from utils import get_tiles
import imagesize


class OneImage(Dataset, ABC):

    def __init__(self,
                 image_path=None,
                 idxs=None,
                 tile_size = None,
                 tile_step = None,
                 crop=None,
                 *args,
                 **kwargs
                 ):

        super().__init__()

        self.image_path = image_path
        self.image_size = imagesize.get(self.image_path)
        self.tile_size = tile_size
        self.tile_step = tile_size if tile_step is None else tile_step
        self.tile_windows = [
            w for w in get_tiles(
                nols=self.image_size[1],
                nrows=self.image_size[0],
                width=self.tile_size[1],
                height=self.tile_size[0],
                col_step=self.tile_step[1],
                row_step=self.tile_step[0]
            )
        ]
        self.idxs = list(range(len(self.tile_windows))) if idxs is None else idxs
        self.crop = crop

    def __len__(self):

        return len(self.idxs)

    def __getitem__(self, idx):

        tile_idx = self.idxs[idx]
        tile_window = self.tile_windows[tile_idx]

        col_offset = tile_window.col_off
        row_offset = tile_window.row_off
        tile_height, tile_width = self.tile_size
        cx = np.random.randint(col_offset, col_offset + tile_width - self.crop + 1)
        cy = np.random.randint(row_offset, row_offset + tile_height - self.crop + 1)
        window = Window(cx, cy, self.crop, self.crop)

        with rasterio.open(self.image_path) as image_file:

            image = image_file.read(window=window, out_dtype=np.float32) / 255

        return {'image': image, 'window': window}


class OneLabeledImage(OneImage):

    def __init__(self, label_path, labels_formatter, *args, **kwargs):

        super(OneLabeledImage, self).__init__(*args, **kwargs)
        self.label_path = label_path
        self.labels_formatter = labels_formatter

    def __getitem__(self, idx):

        d = super(OneLabeledImage, self).__getitem__(idx)

        with rasterio.open(self.label_path) as label_file:

            label = label_file.read(window=d['window'], out_dtype=np.float32)

        mask = self.labels_formatter(label)

        return {**d, **{'mask': mask}}