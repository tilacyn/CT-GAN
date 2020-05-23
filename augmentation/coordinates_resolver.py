import numpy as np
from abc import abstractmethod
import pandas as pd
from os.path import join as opjoin
from paths import annos_path



class InjectCoordinatesResolver:
    def __init__(self):
        pass

    @abstractmethod
    def resolve(self, path2scan):
        pass


class NpInjectCoordinatesResolver(InjectCoordinatesResolver):
    def __init__(self):
        super().__init__()

    def resolve(self, path2scan):
        path2label = path2scan[:-9] + 'label.npy'
        label = np.load(path2label)
        label = label[0, :-1]
        return label.astype(np.int32)


class MhdInjectCoordinatesResolver(InjectCoordinatesResolver):
    def __init__(self):
        self.label_coordinates = pd.read_csv(annos_path)
        super().__init__()

    def resolve(self, path2scan):
        number = int(path2scan[-7:-4])
        coord = self.label_coordinates.query('seriesuid == {}'.format(number)).to_numpy()[0, 1:-1]
        return np.array([coord[2], coord[1], coord[0]])