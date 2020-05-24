import numpy as np
from abc import abstractmethod
import pandas as pd
from os.path import join as opjoin
from paths import annos_path, src_path
from utils.dicom_utils import world2vox, load_mhd

label_coordinates = pd.read_csv(annos_path)


def get_world_coords(scan_id):
    return label_coordinates.query('seriesuid == {}'.format(scan_id)).to_numpy()[0, 1:-1][::-1]


def has_nodule(scan_id):
    return not label_coordinates.query('seriesuid == {}'.format(scan_id)).empty


def worldToVoxelCoord(worldCoord, origin, spacing):
    stretchedVoxelCoord = np.absolute(worldCoord - origin)
    voxelCoord = stretchedVoxelCoord / spacing
    return voxelCoord


def get_vox_coords(scan_id, label_shift=None):
    if label_shift is None:
        label_shift = [0, 0, 40]
    mhd_file = opjoin(src_path, '{}.mhd'.format(scan_id))
    scan, spacing, orientation, origin, _ = load_mhd(mhd_file)
    world_coords = get_world_coords(scan_id)
    vox_coords = world2vox(world_coords, spacing, orientation, origin)
    return  np.add(label_shift, vox_coords)



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
        super().__init__()

    def resolve(self, path2scan):
        scan_id = int(path2scan[-7:-4])
        coord = get_vox_coords(scan_id)
        return coord
