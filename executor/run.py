from storage_client import StorageClient
from compute_pool import ComputePool
from job import Job

cp = ComputePool()
sc = StorageClient()
j = Job(sc, cp)
print("Job initialized, starting now.......")
j.start_job()
print("job submitted, running now......")
