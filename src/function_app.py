import azure.functions as func
import logging, pyodbc
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="cicdfunc1")
def cicdfunc1(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name == "fetch_sql_data":

        # getting secrets from AKV
        try:
            key_vault_uri = "https://cicd-azure-fn-kv.vault.azure.net/"
            # grab credentials if authenticated through Azure CLI or VS Code
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=key_vault_uri, credential = credential)

            sqlusername = client.get_secret("sqlusr").value
            sqlpassword = client.get_secret("sqlpasswrd").value

        except:
            logging.info("exception when attemping to get secrets from Azure Key Vault")
            return func.HttpResponse("exception when attemping to get secrets from Azure Key Vault", status_code=500)
        
        # connecting to SQL DB
        server = 'tcp:ath-sqlsvr.database.windows.net'
        database = 'FreeDB'
        # indicate in the connection string from Azure portal
        driver = '{ODBC Driver 17 for SQL Server}'

        try:
            # get the connection string from portal: go to Database >> Under Settings: Connection strings >>> ODBC
            sql_conn = pyodbc.connect('DRIVER='+driver+';SERVER='+server +
                                  ',1433;DATABASE='+database+';UID='+sqlusername+';PWD=' + sqlpassword)

        except pyodbc.Error as ex:
            logging.info("exception when attempting to connect to SQL DB")
            logging.info(ex)
            return func.HttpResponse("exception when attempting to connect to SQL DB", status_code=500)

        # executing SQL query
        all_records_qry = "SELECT * FROM autos.inventory"
        car_models = []

        try:
            with sql_conn.cursor() as cursor:
                cursor.execute(all_records_qry)
                rows = cursor.fetchall()

                for row in rows:
                    logging.info(row)
                    car_models.append(row[2])

            return func.HttpResponse(f"{car_models}")

        except pyodbc.Error as ex:
            logging.info("exception when attempting to execute SQL query")
            logging.info(ex)
            return func.HttpResponse("exception when attempting to execute SQL query", status_code=500)
        
  
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. However you didn't pass a relevant request name.",
             status_code=200
        )