import uuid

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

    def reset(self):
        pass

    def read_data(self):
        pass

    def write_data(self):
        pass

    def get_output(self): # only results
        pass
