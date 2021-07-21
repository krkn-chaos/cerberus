import subprocess
import logging


# Invokes a given command and returns the stdout.
# Will stop Cerberus execution with exit code 1.
def invoke(command, timeout=60):
    output = ""
    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True, timeout=timeout)
    except Exception as e:
        logging.error("Failed to run %s" % (command))
        logging.error("Error: " + str(e))
    return output


# Invokes a given command and returns the stdout.
# In case of exception, returns message about the impossibility to execute the command instead of stdout.
# It won't stop Cerberus execution but doesn't guarantee that command returns expected stdout.
def optional_invoke(command):
    try:
        optional_output = subprocess.check_output(command, shell=True, universal_newlines=True)
    except Exception:
        optional_output = "Result is absent."
        logging.info(
            "Optional command '%s' can't be executed, but it's not a problem at all. We can continue." % command
        )

    return optional_output
