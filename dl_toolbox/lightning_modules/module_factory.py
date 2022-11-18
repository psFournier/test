from dl_toolbox.lightning_modules import *


modules = {
    'CE': CE,
    'BCE': BCE,
    'CPS': CPS
}

class ModuleFactory:

    @staticmethod
    def create(name):
        return modules[name]
