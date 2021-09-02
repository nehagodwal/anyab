
import datetime
import os
import yaml
from logging import exception, getLogger

import azure.batch.batch_service_client as batch
import azure.batch.batch_auth as batchauth
import azure.batch.models as batchmodels
from azure.storage.blob import ContainerClient
from azure.storage.blob import BlobServiceClient

import helpers

logger = getLogger(__name__)

config = helpers.read_config()

def create_pool(batch_client, job_id, vm_size, vm_count):
    """Submits a job to the Azure Batch service and adds a simple task.
    :param batch_client: The batch client to use.
    :type batch_client: `batchserviceclient.BatchServiceClient`
    :param str job_id: The id of the job to create.
    """

    # cloud_service_config = batchmodels.CloudServiceConfiguration(
    #     os_family='5')

    # pool_spec = batchmodels.PoolSpecification(
    #             vm_size=vm_size,
    #             target_dedicated_nodes=vm_count,
    #             cloud_service_configuration=cloud_service_config,
    #             enable_inter_node_communication=True)

    image_ref_to_use = batch.models.ImageReference(
                       publisher='microsoft-azure-batch',
                       offer='ubuntu-server-container',
                       sku='20-04-lts',
                       version='latest')

    # Specify a container registry
    container_registry = batch.models.ContainerRegistry(
                         registry_server=config['Registry']['registryserver'],
                         user_name=config['Registry']['username'],
                         password=config['Registry']['password'])
    
    # Create container configuration, prefetching Docker images from the container registry
    container_conf = batch.models.ContainerConfiguration(
                     container_registries =[container_registry])

    vm_config = batch.models.VirtualMachineConfiguration(
                image_reference=image_ref_to_use,
                container_configuration=container_conf,
                node_agent_sku_id='batch.node.ubuntu 20.04')
            
    # pool_info = batchmodels.PoolInformation(
    #         auto_pool_specification=batchmodels.AutoPoolSpecification(
    #         auto_pool_id_prefix="HelloWorld",
    #         pool=pool_spec,
    #         keep_alive=False,
    #         pool_lifetime_option=batchmodels.PoolLifetimeOption.job))
    
    new_pool = batch.models.PoolAddParameter(
                id=config['Pool']['id'],
                virtual_machine_configuration=vm_config,
                vm_size=config['Pool']['poolvmsize'],
                target_dedicated_nodes=config['Pool']['poolvmcount'],
                enable_inter_node_communication=True
                )

    batch_client.pool.add(new_pool)

    pool_info= batch.models.PoolInformation(
               pool_id=config['Pool']['id']
               )

    job = batchmodels.JobAddParameter(
          id=job_id, 
          pool_info=pool_info)
    batch_client.job.add(job)

    # Rabbitmq
    image = config['Registry']['image_rabbitmq']
    task_suffix = image.split('/')[-1]
    #task_id = f'{job_id}_{task_suffix}' 
    run_task(batch_client, job, task_suffix, image, '-p 5672:5672 -p 15672:15672')

    # Worker
    image = config['Registry']['image_worker']
    task_suffix = image.split('/')[-1]
    run_task(batch_client, job, task_suffix, image)

    # Driver
    image = config['Registry']['image_driver']
    task_suffix = image.split('/')[-1]
    run_task(batch_client, job, task_suffix, image)

    
def run_task(batch_client, job, task_id, image, container_run_optns=None):
    task_id = f'{job.id}_{task_id}'
    task_container_settings = batch.models.TaskContainerSettings(
                              image_name=image,
                              container_run_options=container_run_optns
                              )

    task = batchmodels.TaskAddParameter(
        id=task_id,
        command_line='',
        container_settings=task_container_settings
    )

    batch_client.task.add(job_id=job.id, task=task)

def create_blob_container(container_name):
    connection_string = config['Storage']['connectionstring']
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
    
def execute_rabbitmq():
    """Executes the sample with the specified configurations.
    :param global_config: The global configuration to use.
    :type global_config: `configparser.ConfigParser`
    :param sample_config: The sample specific configuration to use.
    :type sample_config: `configparser.ConfigParser`
    """
    # Set up the configuration
    batch_account_key = config['Batch']['batchaccountkey']
    batch_account_name = config['Batch']['batchaccountname']
    batch_service_url = config['Batch']['batchserviceurl']

    should_delete_job = config['Pool']['shoulddeletejob']
    pool_vm_size = config['Pool']['poolvmsize']
    pool_vm_count = config['Pool']['poolvmcount']

    # Print the settings we are running with
    print(config)
    
    credentials = batchauth.SharedKeyCredentials(
        batch_account_name,
        batch_account_key)

    batch_client = batch.BatchServiceClient(
        credentials,
        base_url=batch_service_url)

    # Retry 5 times -- default is 3
    batch_client.config.retry_policy.retries = 5
    job_id = helpers.generate_unique_resource_name("job")
    pool_id = config['Pool']['id']
    container_name = f'{pool_id}-{job_id}'
    print("container name: ", container_name)
    create_blob_container(container_name)

    try:
        create_pool(
            batch_client,
            job_id,
            pool_vm_size,
            pool_vm_count)

        tasks = batch_client.task.list(job_id)
        task_ids = [task.id for task in tasks]
        waiting_task_id = [x for x in task_ids if 'driver' in x][0]

        helpers.wait_for_task_to_complete(
            batch_client,
            job_id,
            waiting_task_id,
            datetime.timedelta(minutes=25))

        helpers.print_task_output(batch_client, job_id, task_ids)
    finally:
        if should_delete_job:
            print("Deleting job: ", job_id)
            batch_client.job.delete(job_id)


if __name__ == '__main__':
    
    execute_rabbitmq()