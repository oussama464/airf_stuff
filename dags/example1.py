from datetime import datetime
from pprint import pprint

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException
from airflow.models import DagRun
from airflow.utils.session import provide_session
from airflow.utils.dates import days_ago
from sqlalchemy import text
from airflow.operators.empty import EmptyOperator

ALLOWED_ROLES = {"Admin", "DataOps"}
default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 10, 1),
}


@provide_session
def check_trigger_role(session=None, **context):
    dag_run = context.get("dag_run")

    # Only perform the check if the DAG run was triggered manually.
    if dag_run.external_trigger:
        # Try to retrieve the user object from the DagRun attribute.
        user = getattr(dag_run, "created_by", None)
        if not user:
            raise AirflowException(
                "Manual DAG run detected but no triggering user found in dag_run.created_by."
            )

        triggered_by = user.username

        # Ensure the user object has roles defined.
        if not hasattr(user, "roles") or not user.roles:
            raise AirflowException(f"User '{triggered_by}' has no roles defined.")

        # Build a set of the user's role names.
        user_roles = {role.name for role in user.roles}
        if not (user_roles & ALLOWED_ROLES):
            raise AirflowException(
                f"User '{triggered_by}' with roles {user_roles} is not allowed to manually trigger this DAG."
            )
        else:
            print(
                f"User '{triggered_by}' with roles {user_roles} is allowed to run this DAG."
            )
    else:
        print("This DAG run is not manual. Skipping user role check.")


def _my_function(**context):
    print("###################")
    dag_run = context.get("dag_run")
    # print(context["dag_run"].run_type)
    # print(context["dag_run"].created_by)
    print(getattr(dag_run, "created_by", None))
    print("###################")
    print(dag_run)


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
    task1 = EmptyOperator(task_id="task_a")
    # task1 = PythonOperator(task_id="check_run_type", python_callable=check_trigger_role)
    task2 = PythonOperator(
        task_id="my_task",
        python_callable=_my_function,
    )
    task1 >> task2
