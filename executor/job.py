from logging import getLogger
import datetime
from pprint import pformat
from user_application.utils.shell_commands import run_cmd2
import uuid, time, subprocess
import pandas as pd

import azure.batch as batch
import azure.batch.batch_auth as batchauth
import azure.batch.models as batchmodels
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobServiceClient
from azure.batch.models import AutoUserSpecification, UserIdentity

import helpers

logger = getLogger(__name__)


class Job:
    """
    Represents a full experiment run and kicks off the
    driver/jobManagerTask using the configs setup by the notebook.
    """

    def __init__(self, storage_client, compute_pool):
        """Initializes the job with id and compute pool
        """
        # initializing the job class with storage and compute pool objects
        self.storage_client = storage_client
        self.compute_pool = compute_pool

        # creating a job id
        #self.job_id = uuid.uuid4().hex
        self.job_id = f'job-{uuid.uuid4().hex}'
        
        # setup job dir for configs and output
        #self.job_path = self.storage_client.setup_job_dir(self.job_id)

        # uploading configs for the job
        #self.storage_client.upload_config(self.job_id)

        # stopping condition for the job
        #self.config = self.storage_client.read_job_config_yaml(self.job_id)
        self.config = self.storage_client.read_config()
        #self.storage_client.deployment_config
        self.stopping_condition = self.config['MLOS']['stopping_condition']
        self.deployment_config = self.config[self.config['deployment']]

        if self.config['deployment'] == "AZURE_BATCH":
            self.pool_id = self.deployment_config['Pool']['id']
            self.container_name = f'{self.pool_id}-{self.job_id}'

        print(self.deployment_config)
        batch_account_key = self.deployment_config['Batch']['batchaccountkey']
        batch_account_name = self.deployment_config['Batch']['batchaccountname']
        batch_service_url = self.deployment_config['Batch']['batchserviceurl']

        should_delete_job = self.deployment_config['Pool']['shoulddeletejob']
        pool_vm_size = self.deployment_config['Pool']['poolvmsize']
        pool_vm_count = self.deployment_config['Pool']['poolvmcount']

        # Print the settings we are running with
        print(self.deployment_config)
        
        credentials = batchauth.SharedKeyCredentials(
            batch_account_name,
            batch_account_key)

        self.batch_client = batch.BatchServiceClient(
            credentials,
            batch_url=batch_service_url)

        #self.create_env_file()

    def get_job_id(self):
        return self.job_id

    def get_pool_id(self):
        return self.pool_id

    def get_start_time(self):
        return self.job_start_time

    def get_job_runtime(self):
        return time.time() - self.job_start_time
    
    def get_consolidated_results(self):
        return pd.read_csv('MLOS_executor_dir/job_1/output/user_task_consolidated_results.csv')

    def status_local(self):
        """Get the status of the job
        """
        f = subprocess.Popen(['tail','-F',"MLOS_executor_dir/job_1/output/driver.log"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        
        time = 0
        while time<10:
            line = f.stdout.readline()
            print(line)
            time=time+1

    def worker_task_status(self):
        """Get the status of the job
        """
        f1 = subprocess.Popen(['tail','-F',"MLOS_executor_dir/job_1/worker_1/output/celery.log"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)                                                                                                                                                       
        time1 = 0
        while time1<10:
            line1 = f1.stdout.readline()
            print(line1)
            time1=time1+1

    def user_task_status(self):
        """Get the status of the job
        """
        f2 = subprocess.Popen(['tail','-F',"MLOS_executor_dir/job_1/output/user_task.log"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)                                                       
        time2 = 0
        while time2<10:
            line2 = f2.stdout.readline()
            print(line2)
            time2=time2+1

    def create_env_file(self):
        local_ip_address = self.config[self.config['deployment']]['local_node_ip_address']
        with open(".env", "w") as f:
            f.write("MASTER_CONTAINER_NAME=driver_container\n")
            f.write(f'HOST_NAME={local_ip_address}\n')
            f.write("MASTER_CONTEXT=/home/azureuser/executor\n")
            f.write("WORKER_CONTAINER_NAME=worker_executor\n")
            f.write("WORKER_HOST_NAME=10.0.0.4\n")
            f.write(f'JOB_MOUNT_DIR={self.job_path}\n')

    def run_setup(self):
        # build the driver container
        self._build_driver()
        # build the master container
        self._build_worker()

    # def start_job(self):
    #     self._build_driver()
    #     self._build_worker()
    #     # launch the worker container
    #     self._launch_worker()
    #     # launch the driver container
    #     self._launch_driver()
    #     #return self.get_job_id()

    def create_pool(self, batch_client, job_id):
        """Submits a job to the Azure Batch service and adds a simple task.
        :param batch_client: The batch client to use.
        :type batch_client: `batchserviceclient.BatchServiceClient`
        :param str job_id: The id of the job to create.
        """

        image_ref_to_use = batch.models.ImageReference(
                        publisher='microsoft-azure-batch',
                        offer='ubuntu-server-container',
                        sku='20-04-lts',
                        version='latest')

        # Specify a container registry
        container_registry = batch.models.ContainerRegistry(
                            registry_server=self.deployment_config['Registry']['registryserver'],
                            user_name=self.deployment_config['Registry']['username'],
                            password=self.deployment_config['Registry']['password'])
        
        # Create container configuration, prefetching Docker images from the container registry
        container_conf = batch.models.ContainerConfiguration(
                        container_registries =[container_registry])

        vm_config = batch.models.VirtualMachineConfiguration(
                    image_reference=image_ref_to_use,
                    container_configuration=container_conf,
                    node_agent_sku_id='batch.node.ubuntu 20.04',
                    node_placement_configuration=batch.models.NodePlacementConfiguration(
                                                 policy=batch.models.NodePlacementPolicyType.regional)
                    )
                
        # pool_spec = batch.models.PoolSpecification(enable_inter_node_communication=True,
        #             vm_size=self.deployment_config['Pool']['poolvmsize'])
        # auto_pool_spec = batch.models.AutoPoolSpecification(
        #                  pool_lifetime_option=batchmodels.PoolLifetimeOption.job, 
        #                  pool=pool_spec
        #                  )
        pool_info= batch.models.PoolInformation(
                  pool_id=self.deployment_config['Pool']['id'],
                  #auto_pool_specification=auto_pool_spec
                )

        public_ip_conf = batch.models.PublicIPAddressConfiguration(
                         provision=batch.models.IPAddressProvisioningType.batch_managed)
        network_conf = batch.models.NetworkConfiguration(public_ip_address_configuration=public_ip_conf)

        task_sched_policy = batch.models.TaskSchedulingPolicy(
                            node_fill_type=batch.models.ComputeNodeFillType.pack)
        new_pool = batch.models.PoolAddParameter(
                    id=self.deployment_config['Pool']['id'],
                    enable_inter_node_communication=True,
                    virtual_machine_configuration=vm_config,
                    vm_size=self.deployment_config['Pool']['poolvmsize'],
                    target_dedicated_nodes=self.deployment_config['Pool']['poolvmcount'],
                    network_configuration=network_conf,
                    task_scheduling_policy=task_sched_policy
                    )

        batch_client.pool.add(new_pool)

        job = batchmodels.JobAddParameter(
            id=job_id, 
            pool_info=pool_info)
        batch_client.job.add(job)

        # Rabbitmq
        image = self.deployment_config['Registry']['image_rabbitmq']
        task_suffix = image.split('/')[-1]
        self.run_task(batch_client, job, task_suffix, image, '-p 5672:5672 -p 15672:15672')

        # Worker
        image = self.deployment_config['Registry']['image_worker']
        task_suffix = image.split('/')[-1]
        self.run_task(batch_client, job, task_suffix, image, f'-v /var/run/docker.sock:/var/run/docker.sock -e CNAME={self.container_name} --privileged')

        # Driver
        image = self.deployment_config['Registry']['image_driver']
        task_suffix = image.split('/')[-1]
        self.run_task(batch_client, job, task_suffix, image, f'-e CNAME={self.container_name} --privileged')

        return new_pool

        
    def run_task(self, batch_client, job, task_id, image, container_run_optns=None):
        task_id = f'{job.id}_{task_id}'
        auto_user_spec = AutoUserSpecification(scope='task', elevation_level='admin')
        user_identity = UserIdentity(auto_user=auto_user_spec)

        task_container_settings = batch.models.TaskContainerSettings(
                                image_name=image,
                                container_run_options=container_run_optns
                                )

        if 'rabbitmq' in task_id:
            user_identity = None

        task = batchmodels.TaskAddParameter(
            id=task_id,
            command_line='',
            container_settings=task_container_settings,
            user_identity=user_identity
        )

        batch_client.task.add(job_id=job.id, task=task)

    def start(self):
        # Set up the configuration

        # Retry 5 times -- default is 3
        self.batch_client.config.retry_policy.retries = 5
        job_id = self.job_id
        pool_id = self.pool_id
        container_name = self.container_name
        print("container name: ", container_name)
        self.storage_client.create_blob_container(self.container_name)

        try:
            pool = self.create_pool(
                self.batch_client,
                job_id)

            #waiting_task_id = [x for x in task_ids if 'master' in x][0]

            # check if pool is created
            while pool.state != batchmodels.PoolState.active:
                print(f'Checking if {self.pool_id} is complete... pool state={pool.state}')

            # helpers.wait_for_task_to_complete(
            #     batch_client,
            #     job_id,
            #     waiting_task_id,
            #     datetime.timedelta(minutes=25))

            #helpers.print_task_output(batch_client, job_id, task_ids)
        except Exception:
            raise Exception


    def delete(self):
        print("Deleting job: ", self.job_id)
        self.batch_client.job.delete(self.job_id)
        print("Deleting pool: ", self.pool_id)
        self.batch_client.pool.delete(self.pool_id)

    def status(self):
        tasks = self.batch_client.task.list(self.job_id)
        task_ids = [task.id for task in tasks]
        helpers.print_task_output(self.batch_client, self.job_id, task_ids)

    def _build_driver(self):
        """
        Builds a driver container
        """
        driver_file = self.config['driver_setup']
        logger.info(f'Building driver using the file: {driver_file}')
        build_cmd_str = f'sudo docker-compose -f {driver_file} build'
        run_cmd2(build_cmd_str)
        logger.info('Driver build completed!')

    def _build_worker(self):
        """
        Builds a worker container
        """
        worker_file = self.config['worker_setup']
        logger.info(f'Building worker using the file: {worker_file}')
        build_cmd_str = f'sudo docker-compose -f {worker_file} build'
        run_cmd2(build_cmd_str)
        logger.info('Worker build completed!')

    def _launch_driver(self):
        """
        Launches driver container
        """
        driver_file = self.config['driver_setup']
        #driver_file = self.compute_pool.deployment['driver_setup']
        logger.info(f'Launching driver using the file: {driver_file}')
        launch_str = f'sudo docker-compose -f {driver_file} config && sudo docker-compose -f {driver_file} up --force-recreate -d'
        #run_cmd2(launch_str)
        subprocess.run(launch_str, shell=True, check=True)
        logger.info('Driver launched successfully!')

    def _launch_worker(self):
        """
        Launches a worker container
        """
        worker_file = self.config['worker_setup']   
        logger.info(f'Launching worker using the file: {worker_file}')
        launch_str = f'sudo docker-compose -f {worker_file} config && sudo docker-compose -f {worker_file} up --force-recreate -d'
        #run_cmd2(launch_str)
        subprocess.run(launch_str, shell=True, check=True)
        logger.info('Worker launched successfully!')

    def _shutdown_driver(self):
        """
        Shutdown a driver container
        """
        driver_file = self.config['driver_setup']
        logger.info(f'Shutting down driver using the file: {driver_file}')
        launch_str = f'sudo docker-compose -f {driver_file} down'
        #run_cmd2(launch_str)
        subprocess.run(launch_str, shell=True, check=True)
        logger.info('Driver shutdown successfully!')

    def _shutdown_worker(self):
        """
        Shutdown a worker container
        """
        worker_file = self.config['worker_setup']
        logger.info(f'Shutting down driver using the file: {worker_file}')
        launch_str = f'sudo docker-compose -f {worker_file} down'
        #run_cmd2(launch_str)
        subprocess.run(launch_str, shell=True, check=True)
        logger.info('Worker shutdown successfully!')

    # def set_environment(self):
    #     yml_fp = os.path.join(config.DOCKER['app_path'], config.DOCKER['master_yml_file'])
    #     with open(yml_fp) as f:
    #         doc = yaml.safe_load(f)
    #     doc['services']['driver']['environment']['JOB_STORAGE_PATH'] = self.job_path
    #     with open(yml_fp, 'w') as f:
    #         yaml.safe_dump(doc, f, default_flow_style=False)
