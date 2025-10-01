import logging
import json
import time
from core.optimizer_service.run import run_pipeline, DataOutput

SLEEP_TIME = 10

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_next_task():
    task_id = "4125494b-7ce7-47e6-9e0b-58cc707cf7c7"
    return task_id


def get_json_by_task(task_id: str):
    if task_id == "4125494b-7ce7-47e6-9e0b-58cc707cf7c7":
        with open("sample_dataset/flights.json", "r") as file:
            data = json.load(file)
    else:
        data = {}
    return data


def save_result(data: DataOutput):
    print(data)


def fail_task(task_id: str):
    print(f"{task_id} is saved as failed")


def main():
    while True:
        logger.info("Choosing next task...")
        task_id = get_next_task()
        print(task_id)
        if not task_id:
            logger.info("No new tasks in DB. Sleeping for {SLEEP_TIME}")
            time.sleep(SLEEP_TIME)
            continue

        logger.info(f"Next task id {task_id}")
        logger.info(f"Getting JSON for task {task_id}")

        input_json = get_json_by_task(task_id)
        logger.info("Running pipeline...")

        is_success, data_output = run_pipeline(task_id, input_json)
        if is_success:
            logger.info(f"Successful optimization of task {task_id}")
            logger.info("Saving the results")
            save_result(data_output)
        else:
            logger.info("Optimization failed. Skipping the task")
            fail_task(task_id)


if __name__ == "__main__":
    main()
