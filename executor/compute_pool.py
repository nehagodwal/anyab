class ComputePool:
    """The ComputePool class setup the required to create a place
    to run a "Job"
    """

    def __init__(self):
        """Initializes the compute pool based on the config for the nodes
        """
        #self.deployment = deployment

    # def create_compute_pool(self,  pool_id, batch_service_client=None):
    #     """get the infomation on compute pool
    #     """
    #     #def create_pool(batch_service_client, pool_id):
    #     """
    #     Creates a pool of compute nodes with the specified OS settings.
    #     :param batch_service_client: A Batch service client.
    #     :type batch_service_client: `azure.batch.BatchServiceClient`
    #     :param str pool_id: An ID for the new pool.
    #     :param str publisher: Marketplace image publisher
    #     :param str offer: Marketplace image offer
    #     :param str sku: Marketplace image sku
    #     """
    #     print('Creating pool [{}]...'.format(pool_id))
    #
    #     # Create a new pool of Linux compute nodes using an Azure Virtual Machines
    #     # Marketplace image. For more information about creating pools of Linux
    #     # nodes, see:
    #     # https://azure.microsoft.com/documentation/articles/batch-linux-nodes/
    #
    #     new_pool = batch.models.PoolAddParameter(
    #         id=self.pool_id,
    #         virtual_machine_configuration=batchmodels.VirtualMachineConfiguration(
    #             image_reference=batchmodels.ImageReference(
    #                 publisher="Canonical",
    #                 offer="UbuntuServer",
    #                 sku="18.04-LTS",
    #                 version="latest"
    #             ),
    #             node_agent_sku_id="batch.node.ubuntu 18.04"),
    #         vm_size=config._POOL_VM_SIZE,
    #         target_dedicated_nodes=config._POOL_NODE_COUNT
    #     )
    #     batch_service_client.pool.add(new_pool)
