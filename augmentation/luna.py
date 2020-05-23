from procedures.attack_pipeline import *
from os.path import join as opjoin
from abc import abstractmethod
from coordinates_resolver import NpInjectCoordinatesResolver, MhdInjectCoordinatesResolver
from procedures.mhd_injector import MhdScanManipulator


def get_aug_service(mode, scan_paths, generator_path, save_dir):
    if mode == 'mhd':
        return MhdAugmentationService(scan_paths, generator_path, save_dir)
    if mode == 'np':
        return NpAugmentationService(scan_paths, generator_path, save_dir)


class AugmentationService:
    '''

    '''
    def __init__(self, scan_paths, generator_path, save_dir):
        self.generator_path = generator_path
        self.save_dir = save_dir
        self.is_vox = None
        self.inject_coords_resolver = self.get_coordinates_resolver()
        inject_coords = [self.inject_coords_resolver.resolve(path2scan) for path2scan in scan_paths]
        self.instances = [Instance(scan_path, inject_coord) for scan_path, inject_coord in
                          zip(scan_paths, inject_coords)]

    def load_generator(self):
        self.injector = self.get_injector()
        self.injector.load_injector()

    def augment(self):
        for instance in self.instances:
            self.injector.load_target_scan(instance.path2scan)
            print(instance.inject_coords)
            self.injector.tamper(instance.inject_coords, isVox=self.is_vox)
            self.injector.save_tampered_scan(self.save_dir, instance.get_save_filename(), 'npy')

    @abstractmethod
    def get_injector(self):
        pass

    @abstractmethod
    def get_coordinates_resolver(self):
        pass


class MhdAugmentationService(AugmentationService):
    def __init__(self, scan_paths, generator_path, save_dir):
        super().__init__(scan_paths, generator_path, save_dir)
        self.is_vox = False

    def get_injector(self):
        return MhdScanManipulator(self.generator_path)

    def get_coordinates_resolver(self):
        return MhdInjectCoordinatesResolver()

class NpAugmentationService(AugmentationService):
    def __init__(self, scan_paths, generator_path, save_dir):
        super().__init__(scan_paths, generator_path, save_dir)
        self.is_vox = True

    def get_injector(self):
        return scan_manipulator(self.generator_path)

    def get_coordinates_resolver(self):
        return NpInjectCoordinatesResolver()



class Instance:
    def __init__(self, path2scan, inject_coord):
        self.path2scan = path2scan
        self.inject_coords = inject_coord

    def get_save_filename(self):
        return 'generated_' + self.path2scan.split('/')[-1]

