"""
App ID: <ENTER_APP_ID_HERE>
Bot user OAuth Access Token: <ENTER_BOT_USER_OAUTH_ACCESS_TOKEN_HERE>
"""

import argparse
import re
from time import sleep, time

from clearml import Task
from clearml.automation.monitor import Monitor
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_API_TOKEN = "<ENTER_BOT_USER_OAUTH_ACCESS_TOKEN_HERE>"
SLACK_CHANNEL = "<ENTER_CHANNEL_NAME_HERE>"


class SlackMonitor(Monitor):
    def __init__(self, min_num_iterations, update_frequency):
        super().__init__()

        self.slack_client = WebClient(token=SLACK_API_TOKEN)

        self.min_num_iterations = min_num_iterations
        self.update_frequency = update_frequency

        self.tasks_being_monitored = {}
        self.last_ongoing_alert_timestamp = time()

    @staticmethod
    def remove_ansi(msg):
        remove_ansi_re = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")
        return remove_ansi_re.sub("", msg)

    def _get_universal_filters(self):
        return {
            "project": self._get_projects_ids(),
        }

    def _get_formatted_console_output(self, task, limit=2**11):
        console_output = task.get_reported_console_output(number_of_reports=3)
        console_output = "\n".join(console_output)
        console_output = self.remove_ansi(console_output)
        return console_output[-limit:]

    def _get_task_details(self, task):
        return (
            f"Project:\t\t\t{task.get_project_name()}\n"
            f"Experiment:\t<{task.get_output_log_web_page()}|{task.name}>\n"
            "Console output:\n"
            f"```\n{self._get_formatted_console_output(task)}\n```"
        )

    def monitor_new(self):
        # Define the filters
        filters = self._get_universal_filters()
        filters.update({"status": ["in_progress"]})

        # Get all relevant tasks
        tasks: list[Task] = Task.get_tasks(task_filter=filters)

        for task in tasks:
            # Check if the task is already being monitored
            if task.id in self.tasks_being_monitored:
                continue

            # Check if required number of iterations is completed
            if self.min_num_iterations and task.get_last_iteration() < self.min_num_iterations:
                continue

            # Post on Slack
            divider = "-----------------------"
            header = ":large_purple_circle: *NEW TASK* :large_purple_circle:"
            details = self._get_task_details(task)

            msg = f"{divider}\n{header}\n{divider}\n\n{details}"
            self.post_message(msg, retries=5)

            print(f"Message posted for experiment {task.get_project_name()} - {task.name}")

            # Add to the set of tasks to be monitored
            self.tasks_being_monitored[task.id] = task.get_last_iteration()

    def monitor_ended(self):
        # Can only alert for those tasks which were already being monitored
        if len(self.tasks_being_monitored) == 0:
            return

        # Define the filters
        allowed_statuses = ["completed", "failed", "stopped"]
        filters = self._get_universal_filters()
        filters.update({"status": allowed_statuses})

        # Get all relevant tasks
        tasks: list[Task] = Task.get_tasks(task_ids=list(self.tasks_being_monitored.keys()), task_filter=filters)

        for task in tasks:
            if task.status not in allowed_statuses:
                continue

            # Post on Slack
            divider = ""
            header = ""
            if task.status == "completed":
                divider = "---------------------------------"
                header = ":large_green_circle: *TASK COMPLETED* :large_green_circle:"
            elif task.status == "failed":
                divider = "--------------------------"
                header = ":red_circle: *TASK FAILED* :red_circle:"
            else:
                divider = "-----------------------------"
                header = ":large_blue_circle: *TASK ABORTED* :large_blue_circle:"
            details = self._get_task_details(task)

            msg = f"{divider}\n{header}\n{divider}\n\n{details}"
            self.post_message(msg, retries=5)

            print(f"Message posted for experiment {task.get_project_name()} - {task.name}")

            # Remove from the set of tasks to be monitored
            self.tasks_being_monitored.pop(task.id)

    def monitor_ongoing(self):
        # Define the filters
        filters = self._get_universal_filters()
        filters.update({"status": ["in_progress"]})

        # Get all relevant tasks
        tasks: list[Task] = Task.get_tasks(task_ids=list(self.tasks_being_monitored.keys()), task_filter=filters)

        if len(tasks):
            # Post heading on Slack
            divider = "-------------------------------"
            header = ":large_orange_circle: *ONGOING TASKS* :large_orange_circle:"
            msg = f"{divider}\n{header}\n{divider}\n"
            self.post_message(msg, retries=5)

            for task in tasks:
                # Post on Slack
                warning = ""
                if task.get_last_iteration() == self.tasks_being_monitored[task.id]:
                    warning = ":warning: ALERT :warning:\nNo progress since last alert"
                details = self._get_task_details(task)

                msg = f"{warning}\n{details}"
                self.post_message(msg, retries=5)

                print(f"Message posted for experiment {task.get_project_name()} - {task.name}")

                # Add to the set of tasks to be monitored
                self.tasks_being_monitored[task.id] = task.get_last_iteration()

    def monitor_step(self):
        # Monitor tasks that have ended
        self.monitor_ended()

        # Monitor new tasks
        self.monitor_new()

        # Monitor tasks that are ongoing every self.update_frequency mins
        if self._timestamp - self.last_ongoing_alert_timestamp > self.update_frequency * 60:
            self.monitor_ongoing()
            self.last_ongoing_alert_timestamp = time()

    def post_message(self, msg, retries, wait_period=10):
        for i in range(retries):
            if i != 0:
                sleep(wait_period)

            try:
                self.slack_client.chat_postMessage(
                    channel=SLACK_CHANNEL,
                    blocks=[dict(type="section", text={"type": "mrkdwn", "text": msg})],
                    # text="Could not render message.",
                )
                return
            except SlackApiError as e:
                print(f'While trying to send message: "\n{msg}\n"\nGot an error: {e.response["error"]}')


def main():
    print("ClearML experiment monitor Slack service\n")

    # Slack Monitor arguments
    parser = argparse.ArgumentParser(description="ClearML monitor experiments and post Slack Alerts")
    parser.add_argument(
        "--projects",
        type=str,
        default="",
        help="The names of the projects to monitor, use empty for all projects. comma separated.",
    )
    parser.add_argument(
        "--min_num_iterations",
        type=int,
        default=0,
        help="Minimum number of iterations of failed/completed experiment to alert. "
        "This will help eliminate unnecessary debug sessions that crashed right after starting "
        "(default:0 alert on all)",
    )
    parser.add_argument(
        "--update_frequency",
        type=int,
        default=60,
        help="Update ongoing projects every N minutes (default: 60)",
    )
    parser.add_argument(
        "--refresh_rate",
        type=float,
        default=10.0,
        help="Set refresh rate of the monitoring service, default every 10.0 sec",
    )

    args = parser.parse_args()

    # create the slack monitoring object
    slack_monitor = SlackMonitor(args.min_num_iterations, args.update_frequency)

    # configure the monitoring filters
    if args.projects:
        args.projects = args.projects.split(",")
        slack_monitor.set_projects(project_names=args.projects)

    # start the monitoring Task
    # Connecting ClearML with the current process,
    # from here on everything is logged automatically
    task = Task.init(project_name="DevOps", task_name="Slack Alerts", task_type=Task.TaskTypes.monitor)  # noqa: F841

    print(f'\nStarting monitoring service\nProject: "{args.projects}"\nRefresh rate: {args.refresh_rate}s\n')

    # Let everyone know we are up and running
    start_message = (
        f"Service up for the following projects: {args.projects}. Frequency of update: {args.update_frequency} minutes."
    )
    slack_monitor.post_message(start_message, retries=1)

    # Start the monitor service, this function will never end
    slack_monitor.monitor(pool_period=args.refresh_rate)


if __name__ == "__main__":
    main()
