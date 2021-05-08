import subprocess
import logging
import sys


# Invokes a given command and returns the stdout.
# Will stop Cerberus execution with exit code 1.
def invoke(command):
    output = ""
    try:
        output = subprocess.check_output(command, shell=True,
                                         universal_newlines=True)
    except Exception:
        logging.error("Failed to run %s" % (command))
        sys.exit(1)
    return output


# Invokes a given command and returns the stdout.
# In case of exception, returns message about the impossibility to execute the command instead of stdout.
# It won't stop Cerberus execution but doesn't guarantee that command returns expected stdout.
def optional_invoke(command):
    try:
        optional_output = subprocess.check_output(command, shell=True,
                                                  universal_newlines=True)
    except Exception:
        optional_output = "Result is absent."
        logging.info(
            "Optional command '%s' can't be executed, but it's not a problem at all. We can continue." % command)

    return optional_output
