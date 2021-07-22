import os
import logging

import cerberus.invoke.command as runcommand


# 'inspect_data' directory is used to collect logs, events and metrics of
# the failed component. Delete 'inspect_data' directory if it exists.
def delete_inspect_directory():
    if os.path.isdir("inspect_data/"):
        logging.info("Deleting existing inspect_data directory")
        runcommand.invoke("rm -R inspect_data")
    runcommand.invoke("mkdir inspect_data")


def inspect_component(namespace):
    dir_name = "inspect_data/" + namespace + "-logs"
    if os.path.isdir(dir_name):
        runcommand.invoke("rm -R " + dir_name)
        logging.info("Deleted existing %s directory" % (dir_name))
    runcommand.invoke("oc adm inspect ns/" + namespace + " --dest-dir=" + dir_name + " | tr -d '\n'")
    logging.info("Inspecting namespace %s into %s" % (namespace, dir_name))


def inspect_operator(operator):
    dir_name = "inspect_data/" + operator + "-logs.out"
    if os.path.isdir(dir_name):
        runcommand.invoke("rm -R " + dir_name)
        logging.info("Deleted existing %s directory" % (dir_name))
    runcommand.invoke("oc adm inspect clusteroperator/" + operator + " --dest-dir=" + dir_name)
    logging.info("Inspecting cluster operator %s into %s" % (operator, dir_name))
