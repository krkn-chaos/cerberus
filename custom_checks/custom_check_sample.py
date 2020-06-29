import logging
import subprocess


def check_name():
    logging.info("Check if number of Ready nodes is greater than 5\n")


def check():
    node_count = subprocess.check_output("oc get nodes | grep Ready | wc -l", shell=True,
                                         universal_newlines=True)
    return True if int(node_count) > 5 else False


def main():
    check_name()
    output = check()
    return output
