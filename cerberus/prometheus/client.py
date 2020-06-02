import logging
import prometheus_api_client
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Initialize the client
def initialize_prom_client(url, token):
    global prom_cli
    bearer = "Bearer " + token
    headers = {'Authorization': bearer}
    try:
        prom_cli = prometheus_api_client.PrometheusConnect(url=url,
                                                           headers=headers,
                                                           disable_ssl=True)
    except Exception as e:
        logging.error("Not able to initialize the client %s" % e)


# Capture the metrics
def get_metrics(query):
    try:
        return prom_cli.custom_query(query=query, params=None)
    except Exception as e:
        logging.error("Failed to get the metrics: %s" % e)
