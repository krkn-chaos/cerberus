import os
import slack
import logging
import datetime
import cerberus.invoke.command as runcommand


# Load env variables and initialize slack python client
def initialize_slack_client():
    try:
        global slack_reporter_token, slack_channel_ID, slack_client
        slack_reporter_token = os.environ["SLACK_API_TOKEN"]
        slack_channel_ID = os.environ["SLACK_CHANNEL"]
        slack_client = slack.WebClient(token=slack_reporter_token)
        logging.info("Slack integration has been enabled")
        return True
    except Exception as e:
        logging.error("Couldn't create slack WebClient. Check if slack env "
                      "varaibles are set. Exception: %s" % (e))
        logging.info("Slack integration has been disabled")
        return False


# Post messages and failures in slack
def post_message_in_slack(slack_message, thread_ts=None):
    slack_client.chat_postMessage(
        channel=slack_channel_ID,
        link_names=True,
        text=slack_message,
        thread_ts=thread_ts
    )


# Get members of a channel
def get_channel_members():
    return slack_client.conversations_members(
        channel=slack_channel_ID
    )


# slack tag to be used while reporitng in slack channel
def slack_tagging(watcher_slack_member_ID, slack_team_alias):
    global slack_tag, valid_watchers
    valid_watchers = get_channel_members()['members']
    if watcher_slack_member_ID in valid_watchers:
        slack_tag = "<@" + watcher_slack_member_ID + ">"
    elif slack_team_alias:
        slack_tag = "@" + slack_team_alias + " "
    else:
        slack_tag = ""


# Report the start of cerberus cluster monitoring in slack channel
def slack_report_cerberus_start(cluster_info, weekday, watcher_slack_member_ID):
    response = slack_client.chat_postMessage(channel=slack_channel_ID,
                                             link_names=True,
                                             text="%s Cerberus has started monitoring! "":skull_and_crossbones: %s" % (slack_tag, cluster_info)) # noqa
    global thread_ts
    thread_ts = response['ts']
    if watcher_slack_member_ID in valid_watchers:
        post_message_in_slack("Hi " + slack_tag + "! The watcher for " + weekday + "!\n", thread_ts)


# Report the nodes and namespace failures in slack channel
def slack_logging(cluster_info, iteration, watch_nodes_status, failed_nodes,
                  watch_cluster_operators_status, failed_operators,
                  watch_namespaces_status, failed_pods_components,
                  custom_checks_status, custom_checks_fail_messages):
    issues = []
    cerberus_report_path = runcommand.invoke("pwd | tr -d '\n'")
    if not watch_nodes_status:
        issues.append("*nodes: " + ", ".join(failed_nodes) + "*")
    if not watch_cluster_operators_status:
        issues.append("*cluster operators: " + ", ".join(failed_operators) + "*")
    if not watch_namespaces_status:
        issues.append("*namespaces: " + ", ".join(list(failed_pods_components.keys())) + "*")
    if not custom_checks_status:
        issues.append("*custom_checks: " + ", ".join(custom_checks_fail_messages) + "*")
    issues = "\n".join(issues)
    post_message_in_slack(slack_tag + " %sIn iteration %d at %s, Cerberus "
                          "found issues in: \n%s \nHence, setting the "
                          "go/no-go signal to false. \nThe full report "
                          "is at *%s* on the host cerberus is running."
                          % (cluster_info, iteration,
                              datetime.datetime.now().replace(microsecond=0).isoformat(),
                              issues, cerberus_report_path), thread_ts)
