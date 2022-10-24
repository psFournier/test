from dl_toolbox.networks import *


networks = {
    'Vgg': Vgg,
    'Unet': Unet
}

class NetworkFactory:

    @staticmethod
    def create(name):
        return networks[name]
