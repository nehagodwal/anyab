import pandas as pd
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Spaces import SimpleHypergrid, ContinuousDimension
from mlos.Optimizers.BayesianOptimizerConfigStore import bayesian_optimizer_config_store
from mlos.Optimizers.BayesianOptimizerFactory import BayesianOptimizerFactory
from tasks import add, run_benchmark_test
from random import randint
from logging import getLogger
import time
import sys, yaml, os
import logging

LOG = "/opt/output/driver.log"
logging.basicConfig(filename=LOG, filemode="w", level=logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger("").addHandler(console)
logger = getLogger(__name__)


class MLOSOptimizer:
    def __init__(self, conf) -> None:
        # single continuous input dimension between 0 and 1
        self.conf = conf
        input_param = self.conf['MLOS']['input_simple_hypergrid']
        output_param = self.conf['MLOS']['output_simple_hypergrid']
        bayesian_opt_config = self.conf['MLOS']['bayesian_optimizer_config']
        self.optimizer_suggestion = None
        self.celery_task_id = None
        self.output_function_value = None

        input_space = SimpleHypergrid(name="input",
                                      #dimensions=[ContinuousDimension(name="shared_buffers", min=128, max=1024)]
                                      dimensions=self.get_dimensions(input_param['dimensions'])
                                      )
        output_space = SimpleHypergrid(name="objective",
                                       #dimensions=[ContinuousDimension(name="avg_latency", min=5, max=15)]
                                       dimensions=self.get_dimensions(output_param['dimensions'])
                                       )

        # define optimization problem with input and output space and objective
        optimization_problem = OptimizationProblem(
            parameter_space=input_space,
            objective_space=output_space,
            # we want to minimize the function
            objectives=[Objective(name=output_param['objective'], minimize=True)]
        )

        # configure the optimizer, start from the default configuration
        optimizer_config = bayesian_optimizer_config_store.default
        # set the fraction of randomly sampled configuration to 10% of suggestions
        optimizer_config.experiment_designer_config.fraction_random_suggestions = bayesian_opt_config['random_suggestions_fraction']
        if bayesian_opt_config['random_forest'] == True:
            # configure the random forest surrogate model
            random_forest_config = optimizer_config.homogeneous_random_forest_regression_model_config
            # refit the model after each observation
            random_forest_config.decision_tree_regression_model_config.n_new_samples_before_refit = bayesian_opt_config['random_forest_refit_sample']
            # Use the best split in trees (not random as in extremely randomized trees)
            random_forest_config.decision_tree_regression_model_config.splitter = bayesian_opt_config['random_forest_splitter']
            # right now we're sampling without replacement so we need to subsample
            # to make the trees different when using the 'best' splitter
            random_forest_config.samples_fraction_per_estimator = bayesian_opt_config['random_forest_samples_fraction_per_estimator']
            # Use 10 trees in the random forest (usually more are better, 10 makes it run pretty quickly)
            random_forest_config.n_estimators = bayesian_opt_config['random_forest_n_estimators']
        # Set multiplier for the confidence bound
        optimizer_config.experiment_designer_config.confidence_bound_utility_function_config.alpha = bayesian_opt_config['random_forest_confidence_bound']

        optimizer_factory = BayesianOptimizerFactory()
        self.optimizer = optimizer_factory.create_local_optimizer(
            optimization_problem=optimization_problem,
            optimizer_config=optimizer_config
        )

        self.results = pd.DataFrame()
        self.input_values_df = None
        self.target_values_df = None

    def get_dimensions(self, dimensions_config):
        dims_list = []
        for dim in dimensions_config:
            if 'continuous' in dim.lower():
                cd = ContinuousDimension(name=dimensions_config[dim]['name'], min=dimensions_config[dim]['min'], max=dimensions_config[dim]['max'])
                dims_list.append(cd)
        return dims_list

    def get_suggestion(self):
        suggested_value = self.optimizer.suggest()
        logger.info(f'MLOSOptimizer suggested value: {suggested_value}')
        self.optimizer_suggestion = round(suggested_value["shared_buffers"])
        self.input_values_df = suggested_value.to_dataframe()
        logger.info(f'MLOSOptimizer suggested value: {self.optimizer_suggestion}')
        return self.input_values_df

    def register_result(self, input_values_df, target_values_df, out_res_file):
        #self.target_values_df = pd.DataFrame({'cpu_time': [target_value]})
        self.optimizer.register(input_values_df, target_values_df)
        res = pd.concat([input_values_df, target_values_df], axis=1)
        res.to_csv(out_res_file, mode='a', header=True)

    def write_data(self, df):
        self.results = pd.concat([self.results, df])

    def get_results(self):
        return self.results

    def submit_benchmark_test(self, iter_num, conf):
        input_param_name = self.conf['MLOS']['input_simple_hypergrid']['dimensions']['ContinuousDimension']['name']
        #output_param_name = self.conf['MLOS']['output_simple_hypergrid']['dimensions']['ContinuousDimension']['name']
        output_param_name = "Average Latency (milliseconds)"
        self.output_function_value = run_and_check_benchmark_test(input_param_name, self.optimizer_suggestion,
                                                                  output_param_name, iter_num, conf)
        return self.output_function_value


def run_and_check_load_task():
    logger.info('Loading the benchmark data (tpcc) into Postgres....')

    celery_id = run_load_task.delay()
    logger.info(f'Submitted task to celery: {celery_id}')

    while celery_id.status != 'SUCCESS':
        print(f'Loading in progress... Sleeping for {sleep_time}s.')
        time.sleep(sleep_time)

    if celery_id.status == 'SUCCESS':
        logger.info('Loading completed!!')
    elif celery_id.status == 'FAILURE':
        logger.critical(f'Error loading the benchmark data: {celery_id.traceback}')
        sys.exit(1)
    else:
        logger.critical(f'Error loading the benchmark data: {celery_id.status}')
        sys.exit(1)


def run_and_check_benchmark_test(input_param_name, suggested_param_value, output_param_name, iter_num, conf):
    logger.info(f'Running benchmark with the inputs: {input_param_name}, {suggested_param_value}, '
                f'{output_param_name}, {iter_num}')

    input_dict = {"INPUT_PARAM_NAME": input_param_name, "SUGGESTED_PARAM_VALUE": suggested_param_value,
                  "OUTPUT_PARAM_VALUE": output_param_name, "ITER_NUM": iter_num}
    #mount_results_loc = os.environ.get('JOB_MOUNT_DIR')
    mount_results_loc = "/home/azureuser/executor/MLOS_executor_dir/job_1/output"
    logger.info(f'Mount output results dir: {mount_results_loc}')
    celery_id = run_benchmark_test.delay('user_task', input_dict, conf['source_dir'], mount_results_loc)
    # celery_id = run_tpcc_benchmark.delay(input_param_name, suggested_param_value, output_param_name, iter_num)
    logger.info(f'Submitted task to celery: {celery_id}')
    while celery_id.status != 'SUCCESS':
        print(f'Benchmark in progress... Sleeping for {sleep_time}s.')
        time.sleep(sleep_time)

    if celery_id.status == 'SUCCESS':
        logger.info('Benchmark completed!!')
    elif celery_id.status == 'FAILURE':
        logger.critical(f'Error loading the benchmark data: {celery_id.traceback}')
        sys.exit(1)
    else:
        logger.critical(f'Error loading the benchmark data: {celery_id.status}')
        sys.exit(1)

    return celery_id.result


if __name__ == "__main__":
    # default values
    sleep_time = 5
    # input_param = {"name": "shared_buffers", "min": 128, "max": 1024}
    # output_param = {"name": "Average Latency (milliseconds)", "min": 2, "max": 20}
    output_results ='/opt/output/user_task_consolidated_results.csv'
    conf_filename = '/opt/executor/config.yaml'
    with open(conf_filename, 'r') as st:
        try:
            conf = yaml.safe_load(st)
        except yaml.YAMLError as e:
            logger.exception(e)
    
    num_iterations = conf['MLOS']['stopping_condition']['iteration_count']
    # load task
    # run_and_check_load_task()
    logger.info(f'Creating MLOSOptimizer ....')
    logger.info(f'Input params: {conf}')
    logger.info(f'Output params: {conf}')
    # initializing the MLOSOptimizer object
    optimizer = MLOSOptimizer(conf)

    # benchmark tasks in iteration
    for i in range(num_iterations):
        # get the suggested value
        in_values_df = optimizer.get_suggestion()

        logger.info(f'Iteration: {i}. Running the benchmark data (tpcc) now. ')
        output_func_value = optimizer.submit_benchmark_test(i, conf)
        logger.info(f'Iteration: {i}. Output function value {output_func_value}')
        target_values_df = pd.DataFrame({conf['MLOS']['output_simple_hypergrid']['objective']: [output_func_value]})
        optimizer.register_result(in_values_df, target_values_df, output_results)

    logger.info('Getting results...')
    #res_df = optimizer.get_results()
    logger.info(f'Writing the results back to: {output_results}')
    #res_df.to_csv(output_results, index=False)
    logger.info('Completed!')
