## Goals

Provide a reasonably flexible abstraction (e.g. so someone could extend it to other targets like AWS in the future if they wanted) for executing lots of tests (tasks) for an optimization experiment (job) at scale (parallel) and remotely.

This would be of most benefit for executing longer running benchmarks (e.g. TPC-C, TPC-H on larger systems).

Data visualization and analysis is still expected to be driven from a notebook, but actual benchmark execution should be asynchronous from it.

## Expected Notebook usage
```
from storage_client import StorageClient
from compute_pool import ComputePool
from job import Job

# Build user task image
uc = user_task('user_task')
uc.build()

# Initialize computePool and storageClient
cp = ComputePool()
sc = StorageClient()

# Initialze Job
j = Job(sc, cp)

# Start Job
j.start_job()

# Status of job
j.status()

# worker task status
j.worker_task_status()

# user task status
j.user_task_status()

# check consolidated results
j.get_consolidated_results()

```

## Python Abstractions

class ComputePool: 

    """The ComputePool class setup the required to create a place 

    to run a "Job".   

    """ 

    def __init__(self, config, batch_service_client): 

        """Initializes the compute pool based on the config for the nodes  

        """ 

 

    def get_compute_pool(self): 

        """get the infomation on compute pool 

        """ 

 

#### enumerate over tasks   
class Job: 

    """Represents a full experiment run and kicks off the 

    driver/jobManagerTask using the configs setup by the notebook. 

    """ 
 

    def __init__(self, compute_pool, storage_client, config): 

        """Initializes the job with id and compute pool 

        """ 

        self.job_id = uuid.uuid4().hex 
 

    def start(self): 

        """start a job. This will triggers a job in the env job will run  

        """ 
 
    def stop(self): 

        """Stop a job. This will hard stop a job in the env job will run  

        """ 

    def status(self):

        """Get the status of the job

        """

    def _build_driver(self): 

        """Builds a driver container 

        """ 
 

    def _build_worker(self): 

        """Builds a worker container 

        """ 
 

    def _launch_driver(self): 

        """Launches driver container 

        """ 
 

    def _launch_driver(self): 

        """Launches a worker container 

        """ 
 

    def _shutdown_driver(self): 

        """Shutdown a driver container 

        """ 


    def _shutdown_worker(self): 

        """Shutdown a worker container 

        """ 

         


class Task: 

    """Represents a task that can be either driver or worker or performance-measurement

    """ 

 

    def __init__(self, config): 

        """Initializes for particular config 

        """ 

        self.task_id = uuid.uuid4().hex 
 

    def build_task(self): 

        """Builds a task container 

        """ 
 

    def launch_task(self): 

        """Launches a task 

        """ 
 

    def get_status(self): 

        """Get status from the container 

        """ 

    def shutdown_task(self): 

        """Shutdown the task container 

        """ 

    def reset():
    def read_data(): 
    def write_data():
    def get_output(): # only results

 

 

class storage_client: 

    """Represents storage where results and input can be collected from 

    """ 


    def __init__(self, config): 

        """Initializes for particular config and creates a directory structure  

        at location provided in the config. 

        """ 
 

    def read_data(self, loc): 

        """Read data from the location 

        """ 
 

    def write_data(self, loc): 

        """Write data on to location 

        """ 


    def clear(self): 

        """Reset the the directory structure to start a fresh 

        """ 

 
Config: 

    """A directory contains the configuration essentials 

    """ 
    Compute_pool
        local.yaml
        azure_batch.yaml
        cloudlab.yaml
        instance_type/

##### this could be for templates purposes.  
    Task
        driver
            /Dockerfile
        worker
            /Dockerfile
            /dbms

    Benchmarks
        oltpbench
            /workloads # contains workload descriptor files
                tpcc.xml.template
                tpch.xml.template

    env.yaml # for env variables used in docker files

 
##### specific instances of DBMS
Container_scripts: 

    """A directory structure to keep scripts related to benchmark setup or parsing that's going to be used in dockerfile
    """
    # inital benchmark setup, generate and load data into dbms, run benchmark
    oltpbench.py
    
    # parse performance stats from input and store it as csv or json that can easily readable in dataframe
    parse_result.py




 