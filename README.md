# DAG: Verificação de Clusters EMR Ativos

Este DAG verifica se há clusters EMR ativos na AWS a cada hora e envia um alerta por e-mail caso encontre clusters em execução. Caso contrário, a DAG realiza uma tarefa "dummy". A verificação é realizada por meio da AWS SDK (Boto3), e as credenciais da AWS e o e-mail de alerta são configuráveis.

# Índice
- [Requisitos](#requisitos)
- [Configuração](#configuração)
- [Descrição do Fluxo](#descrição-do-fluxo)
- [Execução do Projeto](#execução-do-projeto)
- [Autor](#autor)

# Requisitos

- Apache Airflow
- Python 3.x
- Boto3
- ConfigParser

## Dependências do Airflow:
- `python_operator`
- `branch_operator`
- `dummy_operator`
- `email_operator`

## Pacotes necessários:
- `boto3` para interação com os serviços da AWS.
- `configparser` para ler o arquivo de configuração de credenciais da AWS e e-mail.

Para instalar os pacotes necessários é preciso acessar o docker, a seguir um pequeno tutorial:

```
### Verificar os dockers ativos para pegar o nome do container 'worker'
docker ps
```

```
### Acessar o container worker (troque para o nome do container worker)
docker exec -it <nome_do_container> bash
```

```
# instalar bibliotecas necessárias
pip install Boto3 ConfigParser
```

Também será preciso configurar as credenciais para envio de email

```
### Editar o arquivo airflow.cfg
nano /opt/airflow/airflow.cfg
```

```
# Modifique a seção [smtp] e edite com suas configurações SMTP
[smtp]
# Ativar envio de e-mails
smtp_on = True

# Servidor SMTP
smtp_host = smtp.gmail.com

# Porta do servidor SMTP
smtp_port = 587

# Usar TLS (True/False)
smtp_starttls = True

# Usuário do e-mail (exemplo: email@gmail.com)
smtp_user = seu_email@gmail.com

# Senha do e-mail (em geral, é melhor usar senhas de aplicativos)
smtp_password = sua_senha

# E-mail de remetente
smtp_mail_from = seu_email@gmail.com
```
Após editar, salve o arquivo e saia do editor.

Lembrando que essas configurações são para o gmail, [aqui tem um tutorial de como gerar uma senha de aplicativos do gmail](https://support.google.com/accounts/answer/185833?hl=pt-BR).


# Configuração

1. **Arquivo de Configuração**:
   O arquivo de configuração (`aws.cfg`) deve estar presente no diretório `/opt/airflow/config/` e conter as seguintes seções:

    ```ini
    [EMR]
    AWS_ACCESS_KEY_ID = seu_access_key
    AWS_SECRET_ACCESS_KEY = seu_secret_key

    [EMAIL]
    EMAIL = seu_email@dominio.com
    ```

2. **Credenciais AWS**:
   As credenciais da AWS (Access Key ID e Secret Access Key) são usadas para autenticar as requisições feitas ao serviço EMR.

3. **E-mail de Alerta**:
   O e-mail de alerta (definido em `EMAIL`) receberá a notificação sobre a existência de clusters EMR ativos.

# Descrição do Fluxo

- **verificar_clusters_emr**: Função principal que verifica os clusters EMR em estados de "STARTING", "BOOTSTRAPPING", "RUNNING" e "WAITING".
  - Se encontrar clusters ativos, a função envia as informações para o XCom e direciona o fluxo para a tarefa de envio de e-mail.
  - Caso contrário, a DAG segue para a tarefa "dummy", que indica que nenhum cluster está ativo.

- **BranchPythonOperator**: Usado para dividir o fluxo dependendo do resultado da verificação dos clusters EMR.

- **DummyOperator**: Utilizado quando não há clusters EMR ativos.

- **EmailOperator**: Envia um e-mail contendo a lista de clusters ativos, caso existam.

A DAG é executada a cada hora (configuração padrão do parâmetro `schedule_interval`).

### Fluxo de Execução

1. **`check_cluster_branch`**: Esta tarefa verifica se há clusters EMR ativos.
   - Se houver clusters ativos, segue para a tarefa de envio de e-mail.
   - Caso contrário, segue para a tarefa `no_cluster_task` (DummyOperator).

2. **`send_email_task`**: Caso haja clusters ativos, um e-mail será enviado com a lista de clusters em execução.

3. **`no_cluster_task`**: Caso não haja clusters ativos, a DAG não faz nada além de registrar o resultado.

A tarefa branch_task dirige o fluxo para a próxima tarefa, dependendo do resultado.

<img src=https://github.com/KleuberFav/checar_cluster/blob/main/artefatos/fluxo.png/>

### Exemplo de Saída do E-mail

Se houver clusters ativos, o e-mail será similar ao seguinte:

```Assunto: Alerta: Cluster EMR ativo detectado```

Corpo:

    Os seguintes clusters estão ativos:

    ID: j-2H7YPYV42EKP, Nome: Cluster de Teste
    ID: j-3I3LYZM1PRA, Nome: Cluster de Produção

Caso não haja clusters ativos, o fluxo termina sem gerar e-mail.

<img src=https://github.com/KleuberFav/checar_cluster/blob/main/artefatos/email.png/>

# Execução do Projeto

Para rodar o projeto, siga os passos abaixo:

1. **Construa os contêineres**: 
   ```bash
   docker-compose up --build

### Notas Finais

Certifique-se de que as credenciais da AWS e do e-mail estão corretamente configuradas no arquivo aws.cfg. O e-mail de alerta será enviado para o endereço configurado, com informações sobre os clusters EMR ativos.

# Autor
**Kleuber Favacho** - *Engenheiro de Dados, Analista de Dados e Estatístico* 
- [Github](https://github.com/KleuberFav)
- [Linkedin](https://www.linkedin.com/in/kleuber-favacho/)
