import pendulum
import os
import requests
import pandas as pd
from datetime import datetime
from airflow.models import DAG
from airflow.contrib.operators.spark_submit_operator import SparkSubmitOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

spark_master = "spark://spark:7077"
spark_app_name_silver = "Spark_Silver_Layer_Transform"
datalake = '/usr/local/datalake/'
source = 'openbrewerydb'
api_type = 'breweries'

args = {
    'start_date': days_ago(2),
    'email': ['team@example.com'],
    'email_on_failure': False
}



def get_list_breweries():
    print(os.listdir(os.path.join(datalake)))

    if not os.path.exists(os.path.join(datalake,'bronze',source)): 
        os.makedirs(os.path.join(datalake,'bronze',source)) 

    if not os.path.exists(os.path.join(datalake,'bronze',source,api_type)): 
        os.makedirs(os.path.join(datalake,'bronze',source, api_type)) 

    file_path = os.path.join(datalake,'bronze',f'{source}',f'{api_type}',f'breweries_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    print(f'Saving brewery list to datalake folder:{file_path}')
    url = 'https://api.openbrewerydb.org/v1/breweries'
    breweries = requests.get(url).json()
    df_breweries = pd.DataFrame(breweries)
    df_breweries.to_json(file_path, orient='records')


dag = DAG(
    dag_id='ABInbev_Case_Breweries_Ingestion',
    default_args=args,
    schedule_interval=None,
    max_active_runs=1,
    catchup=False
)

start = DummyOperator(task_id="start", dag=dag)

bronze_task_get_list_of_breweries = PythonOperator(
    task_id='bronze_task_get_list_of_breweries',
    provide_context=True,
    python_callable=get_list_breweries,
    dag=dag,
)

silver_task_spark_job = SparkSubmitOperator(
        task_id="silver_task_spark_job",
        application="/usr/local/spark/app/abinbev_silver_transform_spark_job.py",
        name=spark_app_name_silver,
        conn_id="spark_default",
        verbose=1,
        conf={"spark.master":spark_master},
        application_args=None,
        dag=dag
    )

gold_task_spark_job = SparkSubmitOperator(
        task_id="gold_task_spark_job",
        application="/usr/local/spark/app/abinbev_gold_transform_spark_job.py",
        name=spark_app_name_silver,
        conn_id="spark_default",
        verbose=1,
        conf={"spark.master":spark_master},
        application_args=None,
        dag=dag
    )

end = DummyOperator(task_id="end", dag=dag)

start >> bronze_task_get_list_of_breweries >> silver_task_spark_job >> gold_task_spark_job >> end
