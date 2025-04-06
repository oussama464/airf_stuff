from datetime import datetime
from pprint import pprint

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException

default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 10, 1),
}


def _check_trigger_type(**context):
    if context["dag_run"].run_type == "manual":
        raise AirflowException("Manual triggers disabled")


def _my_function(**context):
    print("###################")
    print(context["dag_run"].run_type)
    print("###################")


with DAG(
    "my_dag",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    max_active_runs=1,
    access_control={
        "Op": {
            "DAGs": {"can_read"},
            "DAG Runs": {"can_read"},  # Only view runs, no manual triggers
        },
        "Admin": {
            "DAGs": {"can_read"},
            "DAG Runs": {"can_read"},  # Only view runs, no manual triggers
        },
    },
    tags=["example"],
) as dag:

    task1 = PythonOperator(
        task_id="check_run_type", python_callable=_check_trigger_type
    )
    task2 = PythonOperator(
        task_id="my_task",
        python_callable=_my_function,
    )
    task1 >> task2
