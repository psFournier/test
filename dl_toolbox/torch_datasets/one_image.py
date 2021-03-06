import numpy as np
import rasterio
from rasterio.windows import Window
from torch.utils.data import Dataset
from abc import ABC
from utils import get_tiles
import imagesize
import torch
import augmentations as aug


class OneImage(Dataset, ABC):

    def __init__(self,
                 image_path,
                 label_path=None,
                 idxs=None,
                 tile_size=None,
                 crop_size=None,
                 fixed_crops=False,
                 img_aug=None,
                 *args,
                 **kwargs
                 ):

        super().__init__()

        self.image_path = image_path
        self.label_path = label_path
        width, height = imagesize.get(self.image_path)
        self.tile_size = tile_size
        self.tile_windows = [
            w for w in get_tiles(
                nols=width,
                nrows=height,
                width=self.tile_size[1],
                height=self.tile_size[0],
                col_step=self.tile_size[1],
                row_step=self.tile_size[0]
            )
        ]
        self.fixed_crops = fixed_crops
        if self.fixed_crops:
            self.crop_windows = [
                    w for w in get_tiles(
                        nols=tile_size[1],
                        nrows=tile_size[0],
                        width=crop_size,
                        height=crop_size,
                        col_step=crop_size,
                        row_step=crop_size
                    )
                ]

        self.idxs = list(range(len(self.tile_windows))) if idxs is None else idxs
        self.crop_size = crop_size
        self.img_aug = aug.get_transforms(img_aug)

    def process_image(self, image):

        return torch.from_numpy(image).contiguous() / 255

    def process_label(self, label):

        label = torch.from_numpy(label).contiguous()

        return label, None

    def __len__(self):
            
        if self.fixed_crops:
            return len(self.idxs) * len(self.crop_windows)
        else:
            return len(self.idxs)

    def __getitem__(self, idx):

        if self.fixed_crops:
            tile_idx = self.idxs[idx // len(self.idxs)]
            tile_window = self.tile_windows[tile_idx]
            col_offset = tile_window.col_off
            row_offset = tile_window.row_off
            crop_window = self.crop_windows[idx % len(self.idxs)]
            cx = crop_window.col_off + col_offset
            cy = crop_window.row_off + row_offset
        else:
            tile_idx = self.idxs[idx]
            tile_window = self.tile_windows[tile_idx]
            col_offset = tile_window.col_off
            row_offset = tile_window.row_off
            cx = np.random.randint(col_offset, col_offset + self.tile_size[1] - self.crop_size + 1)
            cy = np.random.randint(row_offset, row_offset + self.tile_size[0] - self.crop_size + 1)
        window = Window(cx, cy, self.crop_size, self.crop_size)
        print(window)

        with rasterio.open(self.image_path) as image_file:
            image = image_file.read(window=window, out_dtype=np.float32)
            image = self.process_image(image)

        label = None
        if self.label_path:
            with rasterio.open(self.label_path) as label_file:
                label = label_file.read(window=window, out_dtype=np.float32)
                label = self.process_label(label)

        if self.img_aug is not None:
            # image needs to be either [0, 255] ints or [0,1] floats
            end_image, end_mask = self.img_aug(img=image, label=label)
        else:
            end_image, end_mask = image, label

        # end_image needs to be float for the nn
        return {'orig_image': image, 'orig_mask': label, 'image': end_image, 'window': window, 'mask': end_mask}
