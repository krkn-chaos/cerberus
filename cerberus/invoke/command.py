import subprocess
import logging
import sys


# Invokes a given command and returns the stdout
def invoke(command):
    output = ""
    try:
        output = subprocess.check_output(command, shell=True,
                                         universal_newlines=True)
    except Exception:
        logging.error("Failed to run %s" % (command))
        sys.exit(1)
    return output
