from airflow.hooks.base_hook import BaseHook
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

SLACK_CONN_ID = "slack_connection_id"


def convert_datetime(datetime_string):
    return datetime_string.strftime("%b-%d %H:%M:%S")


def slack_fail_alert(context):
    """Adapted from https://medium.com/datareply/integrating-slack-alerts-in-airflow-c9dcd155105
    Sends message to a slack channel.
       If you want to send it to a "user" -> use "@user",
           if "public channel" -> use "#channel",
           if "private channel" -> use "channel"
    """

    webhook_token_url = BaseHook.get_connection(SLACK_CONN_ID).password
    channel = BaseHook.get_connection(SLACK_CONN_ID).login
    slack_msg = f"""
        :x: Task Failed.
        *Task*: {context.get('task_instance').task_id}
        *Dag*: {context.get('task_instance').dag_id}
        *Execution Time*: {convert_datetime(context.get('execution_date'))}
        <{context.get('task_instance').log_url}|*Logs*>
    """
    # see https://towardsdatascience.com/integrating-docker-airflow-with-slack-to-get-daily-reporting-c462e7c8828a#:~:text=The%20Slack%20Webhook%20Operator%20can,some%20trigger%20condition%20is%20met. # noqa
    slack_alert = SlackWebhookOperator(
        task_id="slack_failer",
        message=slack_msg,
        channel=channel,
        webhook_token=webhook_token_url,
        username="airflow",
        http_conn_id=SLACK_CONN_ID,
    )

    return slack_alert.execute(context=context)


def slack_success_alert(ti):
    """Adapted from https://medium.com/datareply/integrating-slack-alerts-in-airflow-c9dcd155105
    Sends message to a slack channel.
       If you want to send it to a "user" -> use "@user",
           if "public channel" -> use "#channel",
           if "private channel" -> use "channel"
    """
    urls_demo = ti.xcom_pull(key="urls_demo")
    webhook_token_url = BaseHook.get_connection(SLACK_CONN_ID).password
    channel = BaseHook.get_connection(SLACK_CONN_ID).login
    slack_msg = f"""
        :coche_blanche: Task Success.
        *Task*: {context.get('task_instance').task_id}
        *Dag*: {context.get('task_instance').dag_id}
        *Execution Time*: {convert_datetime(context.get('execution_date'))}
        *Demo Urls*: {urls_demo}
        <{context.get('task_instance').log_url}|*Logs*>
    """
    # see https://towardsdatascience.com/integrating-docker-airflow-with-slack-to-get-daily-reporting-c462e7c8828a#:~:text=The%20Slack%20Webhook%20Operator%20can,some%20trigger%20condition%20is%20met. # noqa
    slack_alert = SlackWebhookOperator(
        task_id="slack_successer",
        message=slack_msg,
        channel=channel,
        webhook_token=webhook_token_url,
        username="airflow",
        http_conn_id=SLACK_CONN_ID,
    )

    return slack_alert.execute(context=context)
