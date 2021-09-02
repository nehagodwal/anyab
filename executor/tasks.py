from logging import getLogger
from celery import Celery
import subprocess
import time, json

host_ip = '10.0.0.4'
app = Celery('tasks', broker='pyamqp://guest@{0}:5672'.format(host_ip), backend='rpc://')

def current_milli_time():
    return round(time.time() * 1000)

@app.task
def add(x, y):
    return x + y


@app.task
def run_benchmark_test(img_name, input_dict, work_dir, results_location):
    # creating a temporary file name
    file_name = f'temp_{round(time.time() * 1000)}.env'
    fd = open(file_name, 'w')
    for k, v in input_dict.items():
        fd.write(f'{k}={v}\n')
    fd.close()

    cmd = f"docker run --env-file={file_name} -v {work_dir}:/opt/executor -v {results_location}:/opt/oltpbench/results {img_name}"

    print('Running docker command using subprocess:', cmd)

    try:
        res = subprocess.run(cmd, shell=True, check=True)
    except Exception as e:
        raise Exception(f'Celery task failed for command {cmd} with the error: {e}')

    # reading the results
    iter_num = input_dict['ITER_NUM']
    output_file_name = f'/opt/executor/MLOS_executor_dir/job_1/output/oltp_results_{iter_num}.summary'

    print('Reading results from: ', output_file_name)

    with open(output_file_name, 'r') as fd:
        j = json.load(fd)

    ret_val = j['Latency Distribution'][input_dict["OUTPUT_PARAM_VALUE"]]
    fd.close()

    print(f'Benchmark results: {output_file_name}, Ret val: {ret_val}')
    return ret_val