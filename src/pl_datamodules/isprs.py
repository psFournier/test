from pytorch_lightning import LightningDataModule
from torch.utils.data import RandomSampler, DataLoader
import numpy as np
from src.datasets import Isprs_labeled, Isprs_unlabeled

class Isprs_semisup(LightningDataModule):

    def __init__(self,
                 data_path,
                 nb_pass_per_epoch,
                 batch_size,
                 sup_train_transforms,
                 val_transforms,
                 unsup_train_transforms
                 ):

        super().__init__()
        self.labeled_idxs = [1, 3, 5, 7, 11, 13, 15, 17, 21, 23, 26, 28, 30, 32,
                          34, 37]
        self.unlabeled_idxs = [2, 4, 6, 8, 10, 12, 14, 16, 20, 22, 24, 27, 29,
                               31, 33, 35, 38]
        self.data_path = data_path
        self.nb_pass_per_epoch = nb_pass_per_epoch
        self.batch_size = batch_size
        self.sup_train_transforms = sup_train_transforms
        self.val_transforms = val_transforms
        self.unsup_train_transforms = unsup_train_transforms

    def prepare_data(self, *args, **kwargs):

        # Nothing to write on disk, data is already there, no hard
        # preprocessing necessary
        pass

    def setup(self, stage=None):

        np.random.shuffle(self.labeled_idxs)
        val_idxs = self.labeled_idxs[:4]
        train_idxs = self.labeled_idxs[4:]

        self.sup_train_set = Isprs_labeled(self.data_path,
                                           train_idxs,
                                           self.sup_train_transforms)

        self.val_set = Isprs_labeled(self.data_path,
                                      val_idxs,
                                      self.val_transforms)

        unsup_train_idxs = train_idxs + self.unlabeled_idxs
        self.unsup_train_set = Isprs_unlabeled(self.data_path,
                                               unsup_train_idxs,
                                               self.unsup_train_transforms)

    def train_dataloader(self):

        num_samples = self.nb_pass_per_epoch*len(self.sup_train_set)
        sup_train_sampler = RandomSampler(
            data_source=self.sup_train_set,
            replacement=True,
            num_samples=num_samples
        )
        sup_train_dataloader = DataLoader(
            dataset=self.sup_train_set,
            batch_size=self.batch_size,
            sampler=sup_train_sampler
        )

        unsup_train_sampler = RandomSampler(
            data_source=self.unsup_train_set,
            replacement=True,
            num_samples=num_samples
        )
        unsup_train_dataloader = DataLoader(
            dataset=self.unsup_train_set,
            batch_size=self.batch_size,
            sampler=unsup_train_sampler
        )
        train_dataloader = zip(sup_train_dataloader, unsup_train_dataloader)

        return train_dataloader

    def val_dataloader(self):

        num_samples = self.nb_pass_per_epoch * len(self.val_set)
        val_sampler = RandomSampler(
            data_source=self.val_set,
            replacement=True,
            num_samples=num_samples
        )
        val_dataloader = DataLoader(
            dataset=self.val_set,
            batch_size=self.batch_size,
            sampler=val_sampler
        )

        return val_dataloader