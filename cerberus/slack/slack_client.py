import slack
import os


# Load env variables and initialize slack python client
def initialize_slack_client():
    global slack_client, slack_reporter_token, slack_channel_name
    slack_reporter_token = os.environ["SLACK_API_TOKEN"]
    slack_channel_name = os.environ["SLACK_CHANNEL"]
    slack_client = slack.WebClient(token=slack_reporter_token)


# Post messages and failures in slack
def post_message_in_slack(slack_message):
    slack_client.chat_postMessage(
        channel=slack_channel_name,
        text=slack_message
    )


# Post cerberus report in slack
def post_file_in_slack():
    slack_client.files_upload(
        channels=slack_channel_name,
        file="cerberus.report"
    )
