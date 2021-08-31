
import datetime
import os
import yaml
from logging import getLogger

import azure.batch._batch_service_client as batch
import azure.batch.batch_auth as batchauth
import azure.batch.models as batchmodels

import helpers

logger = getLogger(__name__)

config = helpers.read_config()

def create_pool(batch_client, job_id, vm_size, vm_count):
    """Submits a job to the Azure Batch service and adds a simple task.
    :param batch_client: The batch client to use.
    :type batch_client: `batchserviceclient.BatchServiceClient`
    :param str job_id: The id of the job to create.
    """

    cloud_service_config = batchmodels.CloudServiceConfiguration(
        os_family='5')
    pool_info = batchmodels.PoolInformation(
        auto_pool_specification=batchmodels.AutoPoolSpecification(
            auto_pool_id_prefix="HelloWorld",
            pool=batchmodels.PoolSpecification(
                vm_size=vm_size,
                target_dedicated_nodes=vm_count,
                cloud_service_configuration=cloud_service_config),
            keep_alive=False,
            pool_lifetime_option=batchmodels.PoolLifetimeOption.job))

    job = batchmodels.JobAddParameter(id=job_id, pool_info=pool_info)

    batch_client.job.add(job)
    run_task(batch_client=batch_client, job=job)

def run_task(batch_client, job):
    task = batchmodels.TaskAddParameter(
        id="HelloWorld",
        command_line=helpers.wrap_commands_in_shell(
            'windows', ['echo Hello world from the Batch Hello world sample!'])
    )

    batch_client.task.add(job_id=job.id, task=task)


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

    should_delete_job = config['DEFAULT']['shoulddeletejob']
    pool_vm_size = config['DEFAULT']['poolvmsize']
    pool_vm_count = config['DEFAULT']['poolvmcount']

    # Print the settings we are running with
    helpers.print_configuration(config)
    helpers.print_configuration(config)

    credentials = batchauth.SharedKeyCredentials(
        batch_account_name,
        batch_account_key)

    batch_client = batch.BatchServiceClient(
        credentials,
        batch_url=batch_service_url)

    # Retry 5 times -- default is 3
    batch_client.config.retry_policy.retries = 5
    job_id = helpers.generate_unique_resource_name("HelloWorld")

    try:
        create_pool(
            batch_client,
            job_id,
            pool_vm_size,
            pool_vm_count)

        helpers.wait_for_tasks_to_complete(
            batch_client,
            job_id,
            datetime.timedelta(minutes=25))

        tasks = batch_client.task.list(job_id)
        task_ids = [task.id for task in tasks]

        helpers.print_task_output(batch_client, job_id, task_ids)
    finally:
        if should_delete_job:
            print("Deleting job: ", job_id)
            batch_client.job.delete(job_id)


if __name__ == '__main__':
    
    execute_rabbitmq()