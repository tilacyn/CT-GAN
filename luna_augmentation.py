from procedures.attack_pipeline import *
from os.path import join as opjoin


class AugmentationService:
    '''

    '''

    def __init__(self, scan_paths, generator_path, save_dir):
        self.generator_path = generator_path
        self.save_dir = save_dir
        self.inject_coords_resolver = InjectCoordinatesResolver()
        inject_coords = [self.inject_coords_resolver.resolve(path2scan) for path2scan in scan_paths]
        self.instances = [Instance(scan_path, inject_coord) for scan_path, inject_coord in
                          zip(scan_paths, inject_coords)]

    def load_generator(self):
        self.injector = scan_manipulator(self.generator_path)
        self.injector.load_injector()

    def augment(self):
        for instance in self.instances:
            self.injector.load_target_scan(instance.path2scan)
            self.injector.tamper(instance.inject_coords, isVox=True)
            self.injector.save_tampered_scan(self.save_dir, instance.get_save_filename())


class Instance:
    def __init__(self, path2scan, inject_coord):
        self.path2scan = path2scan
        self.inject_coords = inject_coord

    def get_save_filename(self):
        return 'generated_' + self.path2scan.split('/')[-1]


class InjectCoordinatesResolver:
    def __init__(self):
        pass

    def resolve(self, path2scan):
        path2label = path2scan[:-9] + 'label.npy'
        label = np.load(path2label)
        return label[0].astype(np.int32)
