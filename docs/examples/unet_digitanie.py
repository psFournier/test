from argparse import ArgumentParser
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning import Trainer 
from pytorch_lightning.profiler import SimpleProfiler
from pytorch_lightning.loggers import TensorBoardLogger
from dl_toolbox.lightning_modules import Unet
from dl_toolbox.lightning_datamodules import DigitanieDm
from dl_toolbox.callbacks import SegmentationImagesVisualisation, ConfMatLogger, CustomSwa


def main():

    parser = ArgumentParser()
    parser.add_argument("--output_dir", type=str, default="./outputs")
    parser = Unet.add_model_specific_args(parser)
    parser = DigitanieDm.add_model_specific_args(parser)
    parser = Trainer.add_argparse_args(parser)
    args = parser.parse_args()
    args_dict = vars(args)

    pl_datamodule = DigitanieDm(**args_dict)
    pl_module = Unet(**args_dict)
    trainer = Trainer.from_argparse_args(
        args,
        logger=TensorBoardLogger(args.output_dir, name='unet_digitanie'),
        profiler=SimpleProfiler(),
        callbacks=[
            ModelCheckpoint(monitor='Val_Dice', mode='min'),
            ModelCheckpoint(),
            SegmentationImagesVisualisation(),
            ConfMatLogger(),
            #CustomSwa(
            #    swa_epoch_start=0.8,
            #    swa_lrs=0.005,
            #    annealing_epochs=1,
            #    annealing_strategy='linear',
            #    device=None
            #)
        ],
        log_every_n_steps=300,
        flush_logs_every_n_steps=1000,
        num_sanity_val_steps=0,
        check_val_every_n_epoch=1,
        benchmark=True
    )

    trainer.fit(model=pl_module, datamodule=pl_datamodule)


if __name__ == "__main__":

    main()
