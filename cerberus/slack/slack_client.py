import slack
import os


# Load env variables and initialize slack python client
def initialize_slack_client():
    global slack_reporter_token, slack_channel_ID, slack_client
    slack_reporter_token = os.environ["SLACK_API_TOKEN"]
    slack_channel_ID = os.environ["SLACK_CHANNEL"]
    slack_client = slack.WebClient(token=slack_reporter_token)


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
