import os
import slack
import logging
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
def post_message_in_slack(slack_message):
    slack_client.chat_postMessage(
        channel=slack_channel_ID,
        link_names=True,
        text=slack_message
    )


# Get members of a channel
def get_channel_members():
    return slack_client.conversations_members(
        channel=slack_channel_ID
    )


# slack tag to be used while reporitng in slack channel
def slack_tagging(cop_slack_member_ID, slack_team_alias):
    global slack_tag, valid_cops
    valid_cops = get_channel_members()['members']
    if cop_slack_member_ID in valid_cops:
        slack_tag = "<@" + cop_slack_member_ID + ">"
    elif slack_team_alias:
        slack_tag = "@" + slack_team_alias + " "
    else:
        slack_tag = ""


# Report the start of cerberus cluster monitoring in slack channel
def slack_report_cerberus_start(cluster_info, weekday, cop_slack_member_ID):
    if cop_slack_member_ID in valid_cops:
        post_message_in_slack("Hi " + slack_tag + "! The cop for " + weekday + "!\n")
    post_message_in_slack(slack_tag + "Cerberus has started monitoring! "
                          ":skull_and_crossbones: %s" % (cluster_info))


# Report the nodes and namespace failures in slack channel
def slack_logging(cluster_info, iteration, watch_nodes_status, failed_nodes,
                  watch_cluster_operators_status, failed_operators,
                  watch_namespaces_status, failed_pods_components):
    issues = []
    cerberus_report_path = runcommand.invoke("pwd | tr -d '\n'")
    if not watch_nodes_status:
        issues.append("*nodes: " + ", ".join(failed_nodes) + "*")
    if not watch_cluster_operators_status:
        issues.append("*cluster operators: " + ", ".join(failed_operators) + "*")
    if not watch_namespaces_status:
        issues.append("*namespaces: " + ", ".join(list(failed_pods_components.keys())) + "*")
    issues = "\n".join(issues)
    post_message_in_slack(slack_tag + " %sIn iteration %d, Cerberus "
                          "found issues in: \n%s \nHence, setting the "
                          "go/no-go signal to false. \nThe full report "
                          "is at *%s* on the host cerberus is running."
                          % (cluster_info, iteration, issues, cerberus_report_path))
