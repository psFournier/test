#import dl_toolbox.augmentations as aug
#
#image_level_aug = {
#    'd4': aug.D4,
#    'hflip': aug.Hflip,
#    'vflip': aug.Vflip,
#    'd1flip': aug.Transpose1,
#    'd2flip': aug.Transpose2,
#    'rot90': aug.Rot90,
#    'rot180': aug.Rot180,
#    'rot270': aug.Rot270,
#    'saturation': aug.Saturation,
#    'sharpness': aug.Sharpness,
#    'contrast': aug.Contrast,
#    'gamma': aug.Gamma,
#    'brightness': aug.Brightness,
#}
#
#batch_level_aug = {
#    'no': aug.NoOp,
#    'mixup': aug.Mixup,
#    'cutmix': aug.Cutmix
#}
#
#def get_image_level_aug(names, p=None, bounds=None):
#
#    kwargs = {}
#    if p is not None:
#        kwargs['p'] = p
#    if bounds is not None:
#        kwargs['bounds'] = bounds
#    l = [image_level_aug[name](**kwargs) for name in names]
#
#    return l
#
#
#def get_batch_level_aug(name):
#
#    return batch_level_aug[name]()
