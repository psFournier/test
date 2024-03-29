from argparse import ArgumentParser
import torch.nn as nn
import pytorch_lightning as pl
from torch.optim import Adam
from torch.optim.lr_scheduler import MultiStepLR
import torch
import torchmetrics.functional as torchmetrics
from dl_toolbox.callbacks import plot_confusion_matrix, plot_calib, compute_calibration_bins, compute_conf_mat, log_batch_images
import numpy as np
from dl_toolbox.networks import NetworkFactory


class BaseModule(pl.LightningModule):

    # Validation step common to all modules if possible

    def __init__(self,
                 initial_lr=0.05,
                 final_lr=0.001,
                 lr_milestones=(0.5,0.9),
                 plot_calib=False,
                 class_names=None,
                 *args,
                 **kwargs):

        super().__init__()
        self.net_factory = NetworkFactory()
        self.initial_lr = initial_lr
        self.final_lr = final_lr
        self.lr_milestones = list(lr_milestones)
        self.plot_calib = plot_calib
        self.class_names = class_names if class_names else [str(i) for i in range(self.num_classes)]

    @classmethod
    def add_model_specific_args(cls, parent_parser):

        parser = ArgumentParser(parents=[parent_parser], add_help=False)
        parser.add_argument("--initial_lr", type=float)
        parser.add_argument("--final_lr", type=float)
        parser.add_argument("--lr_milestones", nargs='+', type=float)
        parser.add_argument("--plot_calib", action='store_true')

        return parser
    
    def configure_optimizers(self):

        self.optimizer = Adam(self.parameters(), lr=self.initial_lr)
        scheduler = MultiStepLR(
            self.optimizer,
            milestones=self.lr_milestones,
            gamma=0.2
        )

        return [self.optimizer], [scheduler]

    def validation_step(self, batch, batch_idx):

        inputs = batch['image']
        labels = batch['mask']
        logits = self.forward(inputs).detach()

        probas = self._compute_probas(logits)
        confidences, preds = self._compute_conf_preds(probas)
        batch['preds'] = preds

        if self.trainer.current_epoch % 10 == 0 and batch_idx == 0:
            log_batch_images(
                batch,
                self.trainer,
                prefix='Val'
            )
            
        stat_scores = torchmetrics.stat_scores(
            preds,
            labels,
            ignore_index=None,
            mdmc_reduce='global',
            reduce='macro',
            num_classes=self.num_classes
        )
        
        conf_mat = compute_conf_mat(
            labels.flatten(),
            preds.flatten(),
            self.num_classes,
            ignore_idx=None
        )

        res = {
            'stat_scores': stat_scores.detach(),
            'conf_mat': conf_mat.detach(),
            'logits': logits.detach()
        }

        if self.plot_calib:
            acc_bins, conf_bins, count_bins = compute_calibration_bins(
                torch.linspace(0, 1, 100 + 1).to(self.device),
                labels.flatten(),
                confidences.flatten(),
                preds.flatten(),
                ignore_idx=None
            )
            res['acc_bins'] = acc_bins.detach()
            res['conf_bins'] = conf_bins.detach()
            res['count_bins'] = count_bins.detach()

        return res

    def validation_epoch_end(self, outs):
        
        stat_scores = [out['stat_scores'] for out in outs]

        class_stat_scores = torch.sum(torch.stack(stat_scores), dim=0)
        f1_sum = 0
        tp_sum = 0
        supp_sum = 0
        nc = 0
        for i in range(self.num_classes):
            if i != self.ignore_index:
                tp, fp, tn, fn, supp = class_stat_scores[i, :]
                if supp > 0:
                    nc += 1
                    f1 = tp / (tp + 0.5 * (fp + fn))
                    #self.log(f'Val_f1_{i}', f1)
                    f1_sum += f1
                    tp_sum += tp
                    supp_sum += supp
        
        self.log('Val_acc', tp_sum / supp_sum)
        self.log('Val_f1', f1_sum / nc) 

        conf_mats = [out['conf_mat'] for out in outs]

        cm = torch.stack(conf_mats, dim=0).sum(dim=0).cpu()
        
        #sum_col = torch.sum(cm,dim=1, keepdim=True)
        #sum_lin = torch.sum(cm,dim=0, keepdim=True)
        #if self.ignore_index >= 0: sum_lin -= cm[self.ignore_index,:]
        #cm_recall = torch.nan_to_num(cm/sum_col, nan=0., posinf=0., neginf=0.)
        #cm_precision = torch.nan_to_num(cm/sum_lin, nan=0., posinf=0., neginf=0.)
        #cm_recall = np.divide(cm, sum_col, out=np.zeros_like(cm), where=sum_col!=0)
        #cm_precision = np.divide(cm, sum_lin, out=np.zeros_like(cm), where=sum_lin!=0)
               
        self.trainer.logger.experiment.add_figure(
            "Precision matrix", 
            plot_confusion_matrix(
                cm,
                class_names=self.class_names,
                norm='precision'
            ), 
            global_step=self.trainer.global_step
        )
        self.trainer.logger.experiment.add_figure(
            "Recall matrix", 
            plot_confusion_matrix(
                cm,
                class_names=self.class_names,
                norm='recall'
            ), 
            global_step=self.trainer.global_step
        )

        if self.plot_calib:
            count_bins = torch.stack([out['count_bins'] for out in outs])
            conf_bins = torch.stack([out['conf_bins'] for out in outs])
            acc_bins = torch.stack([out['acc_bins'] for out in outs])
            
            counts = torch.sum(count_bins, dim=0)
            accs = torch.sum(torch.mul(acc_bins, count_bins), dim=0)
            accs = torch.div(accs, counts)
            confs = torch.sum(torch.mul(conf_bins, count_bins), dim=0)
            confs = torch.div(confs, counts)

            figure = plot_calib(
                counts.cpu().numpy(),
                accs.cpu().numpy(),
                confs.cpu().numpy(),
                max_points=10000
            )

            self.trainer.logger.experiment.add_figure(
                f"Calibration",
                figure,
                global_step=self.trainer.global_step
            )


    def on_train_epoch_end(self):
        for param_group in self.optimizer.param_groups:
            self.log(f'learning_rate', param_group['lr'])
            break
