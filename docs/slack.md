# Slack Integration

The user has the option to enable/disable the slack integration ( disabled by default ). To use the slack integration, the user has to first create an [app](https://api.slack.com/apps?new_granular_bot_app=1) and add a bot to it on slack. SLACK_API_TOKEN and SLACK_CHANNEL environment variables have to be set. SLACK_API_TOKEN refers to Bot User OAuth Access Token and SLACK_CHANNEL refers to the slack channel ID the user wishes to receive the notifications. Make sure the Slack Bot Token Scopes contains this permission [calls:read] [channels:read] [chat:write] [groups:read] [im:read] [mpim:read]
- Reports when cerberus starts monitoring a cluster in the specified slack channel.
- Reports the component failures in the slack channel.
- A watcher can be assigned for each day of the week. The watcher of the day is tagged while reporting failures in the slack channel instead of everyone. (NOTE: Defining the watcher id's is optional and when the watcher slack id's are not defined, the slack_team_alias tag is used if it is set else no tag is used while reporting failures in the slack channel.)

#### Go or no-go signal
When the cerberus is configured to run in the daemon mode, it will continuosly monitor the components specified, runs a simple http server at http://0.0.0.0:8080 and publishes the signal i.e True or False depending on the components status. The tools can consume the signal and act accordingly.

#### Failures in a time window
1. The failures in the past 1 hour can be retrieved in the json format by visiting http://0.0.0.0:8080/history.
2. The failures in a specific time window can be retrieved in the json format by visiting http://0.0.0.0:8080/history?loopback=<interval>.
3. The failures between two time timestamps, the failures of specific issues types and the failures related to specific components can be retrieved in the json format by visiting http://0.0.0.0:8080/analyze url. The filters have to be applied to scrape the failures accordingly.
