from executor.config.tpcc_config import TPCCConfig
from executor.config.pg_config import PostgresConfig
from executor.user_application.param_tuning.run_oltp_bench import TPCCParam
from executor.user_application.param_tuning.postgre_param import PostgresParam
from logging import getLogger
import os, logging


LOG = "/opt/oltpbench/results/user_task.log"
logging.basicConfig(filename=LOG, filemode="w", level=logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger("").addHandler(console)
logger = getLogger(__name__)


def run_load_task():
    logger.info('Running load task!!')
    tc = TPCCConfig('executor/user_application/postgres.conf')
    t = TPCCParam(tc)
    t.load_data()
    logger.info('Loading completed!')


def run_tpcc_benchmark():
    run_load_task()
    input_param_name = os.environ['INPUT_PARAM_NAME']
    suggested_param_value = os.environ['SUGGESTED_PARAM_VALUE']
    output_param_name = os.environ['OUTPUT_PARAM_VALUE']
    iter_num = os.environ['ITER_NUM']

    logger.info('Running tpcc benchmark!!')

    # initializing the config
    tc = TPCCConfig('executor/user_application/postgres.conf')
    pc = PostgresConfig('executor/user_application/postgres.conf')

    # initializing the parameter class
    t = TPCCParam(tc)
    p = PostgresParam(pc)

    # updating the param
    p.update_param_value(input_param_name, suggested_param_value, True, False)

    # run the benchmark
    return_val = t.run_benchmark(output_param_name, iter_num)
    logger.info(f'Benchmark task completed: {return_val}')

    return return_val


def main():
    ret_val = run_tpcc_benchmark()
    return ret_val


if __name__ == "__main__":
    main()
