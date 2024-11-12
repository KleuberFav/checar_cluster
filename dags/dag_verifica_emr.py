from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.email import EmailOperator
from datetime import datetime, timedelta
from configparser import ConfigParser
import boto3

# Lê o arquivo de configuração para obter as credenciais da AWS e o e-mail de alerta
config = ConfigParser()
config.read_file(open('/opt/airflow/config/aws.cfg'))
aws_access_key_id = config.get('EMR', 'AWS_ACCESS_KEY_ID')
aws_secret_access_key = config.get('EMR', 'AWS_SECRET_ACCESS_KEY')
to_email = config.get('EMAIL', 'EMAIL')

def verificar_clusters_emr(**kwargs):
    # Inicializa o cliente EMR com as credenciais especificadas
    emr_client = boto3.client(
        'emr',
        region_name='us-east-1',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    
    # Lista clusters em estados de execução ou espera
    clusters = emr_client.list_clusters(ClusterStates=['STARTING', 'BOOTSTRAPPING', 'RUNNING', 'WAITING'])
    
    # Verifica se existe algum cluster ativo e armazena o nome e ID
    cluster_info = []
    if clusters['Clusters']:
        print("Clusters EMR ativos:")
        for cluster in clusters['Clusters']:
            cluster_id = cluster['Id']
            cluster_name = cluster['Name']
            print(f"ID: {cluster_id}, Nome: {cluster_name}")
            cluster_info.append(f"ID: {cluster_id}, Nome: {cluster_name}")
        
        # Armazena as informações dos clusters no XCom
        kwargs['ti'].xcom_push(key='cluster_info', value=cluster_info)
        return 'send_email_task'  # Direciona para a tarefa de envio de e-mail
    else:
        print("Não há clusters EMR ativos no momento.")
        return 'no_cluster_task'  # Direciona para o DummyOperator caso não haja clusters

# Define argumentos padrão da DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Inicializa a DAG
with DAG(
    'check_emr_clusters',
    default_args=default_args,
    description='Verifica se há clusters EMR ativos',
    schedule_interval=timedelta(hours=1),  # Ajuste para a frequência desejada
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    # Tarefa de branch para decidir se há clusters ativos
    branch_task = BranchPythonOperator(
        task_id='check_cluster_branch',
        python_callable=verificar_clusters_emr
    )

    # Tarefa dummy para o caso onde não há clusters ativos
    no_cluster_task = DummyOperator(
        task_id='no_cluster_task'
    )

    # Tarefa de envio de e-mail caso haja clusters ativos
    send_email_task = EmailOperator(
        task_id='send_email_task',
        to=to_email,
        subject="Alerta: Cluster EMR ativo detectado",
        html_content="""
        <p>Os seguintes clusters estão ativos:</p>
        <p>{{ task_instance.xcom_pull(task_ids='check_cluster_branch', key='cluster_info') | join('<br>') }}</p>
        """

    )

    # Define a sequência de execução da DAG
    branch_task >> [send_email_task, no_cluster_task]
