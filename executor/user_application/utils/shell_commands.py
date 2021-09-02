import subprocess
import traceback
import sys
from logging import getLogger

logger = getLogger(__name__)

def run_cmd(cmd_str):
    logger.info(f'Running the sub process command: {cmd_str}')
    try:
        r = subprocess.check_call(cmd_str.split(), stdout=sys.stdout, stderr=subprocess.STDOUT)
        if r != 0:
            raise Exception(f'Called sub process {cmd_str} failed with return code {r}')
    except subprocess.CalledProcessError as e:
        logger.critical(traceback.format_exc())
        raise Exception(f'Called sub process failure for command {cmd_str}. Error: {e}')

def run_cmd2(cmd_str):
    logger.info(f'Running the sub process command: {cmd_str}')
    p = subprocess.Popen(cmd_str.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result, err = p.communicate()
    if p.returncode != 0:
        raise IOError(err)
    logger.info(f'Cmd2 result: {result}')
    return result
