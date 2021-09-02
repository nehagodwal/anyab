from logging import getLogger
from executor.config.tpcc_config import TPCCConfig
from executor.user_application.utils.shell_commands import run_cmd, run_cmd2
import os
import json

logger = getLogger(__name__)


class TPCCParam:
    def __init__(self, tpcc_config : TPCCConfig):
        self.tpcc_config = tpcc_config

    def load_data(self):
        cwd = os.getcwd()
        os.chdir(self.tpcc_config.tpccdir)
        cmd_str = './oltpbenchmark -b {0} -c {1} --create=true --load=true'.format(self.tpcc_config.benchmark,
                                                                                   self.tpcc_config.config_file)
        run_cmd2(cmd_str)
        os.chdir(cwd)
        logger.info('Loading data into the TPCC database')

    def run_benchmark(self, output_param_name, iter_num):
        cwd = os.getcwd()
        os.chdir(self.tpcc_config.tpccdir)
        output_file_name = f'{self.tpcc_config.output_file}_{iter_num}'
        cmd_str = './oltpbenchmark -b {0} -c {1} --execute=true -s {2} -o {3}'.format(self.tpcc_config.benchmark,
                                                                                      self.tpcc_config.config_file,
                                                                                      self.tpcc_config.sample,
                                                                                      output_file_name)
        run_cmd2(cmd_str)

        logger.info(f'Current working directory: {os.getcwd()}')

        # reading the results
        with open(f'results/{output_file_name}.summary', 'r') as fd:
            j = json.load(fd)

        ret_val = j['Latency Distribution'][output_param_name]
        fd.close()

        os.chdir(cwd)
        logger.info(f'Benchmark results: {self.tpcc_config.output_file}, Ret val: {ret_val}')
        return ret_val
