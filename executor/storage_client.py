from logging import getLogger
from pprint import pformat
import yaml, os, shutil
import azure.batch.batch_service_client as batch
import azure.batch.batch_auth as batchauth
import azure.batch.models as batchmodels
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobServiceClient


logger = getLogger(__name__)


class StorageClient:
    """
    Represents storage where results and input can be collected from
    """

    def __init__(self):
        """
            Initializes for particular config and creates a directory structure
            at location provided in the config.
        """
        config = self.read_config()
        self.deployment = config['deployment']
        self.deployment_config = config[self.deployment]
        logger.info(f'Initializing storage client with the {self.deployment} deployment config {pformat(self.deployment_config)}')

        # get the MLOS config from the user else default it from the deployment config file
        # self.mlos_config = config['MLOS']
        # logger.info(f'Initializing storage client with the MLOS config {pformat(self.mlos_config)}')

        # setup the mount path
        if self.deployment == "LOCAL":
            self.mount_dir = self.setup_mount()
            logger.info(f'Mount directory setup completed: {self.mount_dir}')
 
    def create_blob_container(self, container_name):
        connection_string = self.deployment_config['Storage']['connectionstring']
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        # Instantiate a new ContainerClient
        container_client = blob_service_client.get_container_client(container_name)

        try:
            # Create new container in the service
            container_client.create_container()

            # List containers in the storage account
            list_response = blob_service_client.list_containers()
            print(list_response)
        except:
            raise Exception(exception)

    def read_config(self, file='config.yaml'):
        """
        Read config file
        """
        with open(file, 'r') as st:
            try:
                return yaml.safe_load(st)
            except yaml.YAMLError as e:
                logger.exception(e)

    def read_data(self, loc):
        """
        Read data from the location
        """
        pass

    def setup_mount(self):
        """
        """
        logger.info('Setting up the mount directory!')
        # set the mount parent directory
        mount_parent_dir =  self.deployment_config['mount_point'] if self.deployment_config['mount_point'] \
            else os.getcwd()
        logger.info(f'Mount parent directory: {mount_parent_dir}')

        # set the mount path
        mount_path = os.path.join(mount_parent_dir, 'MLOS_executor_dir')
        logger.info(f'Mount path: {mount_path}')

        # make the required directory structure and raise an exception if something bad happens
        try:
            logger.info("Creating the mount directory path if doesnt exist...")
            os.makedirs(mount_path, exist_ok=True)
        except OSError as e:
            logger.error(f'Error creating directory {mount_path}. Exception: {e}')
            raise Exception(f'Error creating directory {mount_path}. Exception: {e}')

        return mount_path

    def get_path(self, p):
        path = os.path.join(self.mount_dir, p)
        logger.info(f'Path returned: {path}')
        return path

    def setup_job_dir(self, job_id):
        job_name = f'job_{job_id}'
        logger.info(f'Setting up the job directory for the job id: {job_id}, job_name: {job_name}')

        job_output_path = os.path.join(job_name, 'output')
        job_config_path = os.path.join(job_name, 'config')
        job_tasks_path = os.path.join(job_name, 'worker_tasks')

        logger.info(f'Setting up the following paths: {job_output_path}, {job_config_path}, {job_tasks_path}')

        try:
            os.makedirs(self.get_path(job_name))
            os.makedirs(self.get_path(job_output_path))
            os.makedirs(self.get_path(job_config_path))
            os.makedirs(self.get_path(job_tasks_path))
            logger.info(f'Paths created for the job {job_id}, {job_name}')
        except OSError as e:
            logger.error(f'Something is wrong with the directory structure: {self.mount_dir}. Error: {e}')
            raise Exception(f'Something is wrong with the directory structure: {self.mount_dir}. Error: {e}')

        return self.get_path(job_name)

    def read_job_config_yaml(self, job_id):
        # setting up the file path given the file name and the job id
        job_name = f'job_{job_id}'
        file_name = os.path.join(job_name, 'config', 'config.yaml')
        logger.info(f'For the job {job_name} reading the file: {file_name}')

        file_path = self.get_path(file_name)
        conf = self.read_config(file_path)

        logger.info(f'Returning the file data: {pformat(conf)}')
        return conf

    def upload_config(self, job_id):
        """
        Upload config files to the storage mount location specified by user
        """
        job_name = f'job_{job_id}'
        job_config_path = os.path.join(job_name, 'config')
        logger.info(f'Uploading the configs to the job {job_name} at path: {job_config_path}')

        path = self.get_path(job_config_path)
        # copy config.yaml to mount path for a particular job
        shutil.copy2('config.yaml', path)
        logger.info('Uploaded config to {path}')

    def setup_task_dir(self, taskid):
        task = f'task-{taskid}'
        self.task_inputs_path = os.path.join(task, 'inputs')
        self.task_ouputs_path = os.path.join(task, 'outputs')
        tasks_path = self.get_path(self.job_tasks_path)
        if os.path.exists(tasks_path):
            try:
                os.makedirs(os.path.join(tasks_path, task))
                os.makedirs(os.path.join(tasks_path, self.task_inputs_path))
                os.makedirs(os.path.join(tasks_path, self.task_ouputs_path))
            except OSError as e:
                raise
        return os.path.join(tasks_path, task)
