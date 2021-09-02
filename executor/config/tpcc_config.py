from executor.config.config import Config


class TPCCConfig(Config):
    def __init__(self, conf_path, section='OLTPBench'):
        super().__init__(conf_path)
        self.config_dict = dict(self.config.items(section))

    @property
    def tpccdir(self):
        return self.get_parameter_value('oltpdir')

    @property
    def benchmark(self):
        return self.get_parameter_value('benchmark')

    @property
    def sample(self):
        return self.get_parameter_value('sample')

    @property
    def output_file(self):
        return self.get_parameter_value('output_file')

    @property
    def config_file(self):
        return self.get_parameter_value('config_file')
