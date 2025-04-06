from airflow.models import DAG


from datetime import datetime


from airflow.operators.empty import EmptyOperator

with DAG(
    "a_dag", start_date=datetime(2021, 1, 1), schedule_interval="@daily", catchup=False
) as dag:
    task_a = EmptyOperator(task_id="task_a")

    task_b = EmptyOperator(task_id="task_b")

    task_c = EmptyOperator(task_id="task_c")

    task_a >> task_b >> task_c
