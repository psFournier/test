from argparse import ArgumentParser
from pytorch_lightning.callbacks import ModelCheckpoint, LearningRateMonitor, StochasticWeightAveraging
from pytorch_lightning import Trainer, loggers
from pytorch_lightning.profiler import AdvancedProfiler, SimpleProfiler
from lightning_modules import *
from lightning_datamodules import *
from callbacks import SegmentationImagesVisualisation, CustomSwa

modules = {
    'sup': SupervisedBaseline,
    'MT': MeanTeacher
}


datamodules = {
    'pan': {
        'sup': PhrPanDm,
        'mt': PhrPanDmSemisup
    }
}

def main():

    # Reading parameters
    parser = ArgumentParser()

    parser.add_argument("--datamodule", type=str, default='mw')
    parser.add_argument("--module", type=str, default="sup")
    parser.add_argument("--output_dir", type=str, default="./outputs")
    parser.add_argument("--exp_name", type=str)

    # Datamodule and module classes add their own specific command line
    # arguments, so we retrieve them to go further with the parser.
    args = parser.parse_known_args()[0]
    parser = modules[args.module].add_model_specific_args(parser)
    parser = datamodules[args.datamodule][args.module].add_model_specific_args(parser)


    # The Trainer class also enables to add many arguments to customize the
    # training process (see Lightning Doc)
    parser = Trainer.add_argparse_args(parser)

    args = parser.parse_args()
    args_dict = vars(args)

    # Logs will be stored in the directory 'tensorboard' of the output
    # directory, and the individual log of each new run will be stored in a
    # subdirectory with the datetime as name. The parameters corresponding to
    # the run can be retrieved in Tensorboard.
    tensorboard = loggers.TensorBoardLogger(
        save_dir=args.output_dir,
        name=args.exp_name,
        default_hp_metric=False
    )

    # Callback to log the learning rate
    lr_monitor = LearningRateMonitor()

    # Callback that saves the weight of the epoch with the minimal val_loss
    # (questionable) at the end of training.
    last_2_epoch_ckpt = ModelCheckpoint(
        monitor='epoch',
        mode='max',
        save_top_k=2,
        verbose=True
    )

    # best_val_loss_ckpt = ModelCheckpoint(
    #     monitor='Val_loss',
    #     mode='min',
    #     save_top_k=1,
    #     verbose=True,
    #     filename='{epoch}-{val_loss:.2f}'
    # )

    # Callback that performs Stochastic Weight Averaging at the end of
    # training
    # swa = StochasticWeightAveraging(
    #     device=None,
    #     # swa_epoch_start=1
    # )
    swa = CustomSwa(
        device=None
    )

    # Monitoring time spent in each call. Difficult to understand the data
    # loading part when multiple workers are at use.
    profiler = SimpleProfiler()

    image_visu = SegmentationImagesVisualisation()

    # Using from_argparse_args enables to use any standard parameter of the
    # lightning Trainer class without having to manually add them to the parser.
    trainer = Trainer.from_argparse_args(
        args,
        logger=tensorboard,
        profiler=profiler,
        callbacks=[
            last_2_epoch_ckpt,
            # best_val_loss_ckpt,
            lr_monitor,
            # swa,
            image_visu
        ],
        log_every_n_steps=300,
        flush_logs_every_n_steps=1000,
        num_sanity_val_steps=0,
        check_val_every_n_epoch=1,
        benchmark=True,
        stochastic_weight_avg=True
   )

    # The lightning datamodule deals with instantiating the proper dataloaders.
    pl_datamodule = datamodules[args.datamodule][args.module](**args_dict)

    # The lightning module is where the training schema is implemented. Class
    # weights are a property of the dataset being processed, given by its class.
    # args_dict['class_weights'] = datamodules[args.datamodule][args.module].class_weights
    pl_module = modules[args.module](**args_dict)

    trainer.fit(model=pl_module, datamodule=pl_datamodule)


if __name__ == "__main__":

    main()
