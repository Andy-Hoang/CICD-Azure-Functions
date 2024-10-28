import azure.functions as func
import logging, pyodbc
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="cicdfunc1")
def cicdfunc1(req: func.HttpRequest) -> func.HttpResponse:

    logging.info("Python HTTP trigger function processed a request.")

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            logging.exception("Param 'name' is expected")
            return func.HttpResponse("Param 'name' is expected", status_code=500)
        else:
            name = req_body.get('name')

    if name == "fetch_sql_data":
        try:
            logging.info('Getting secrets from Azure Key Vault')

            key_vault_uri = "https://cicd-azure-fn-kv.vault.azure.net/"
            # grab credentials if authenticated through Azure CLI or VS Code
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=key_vault_uri, credential = credential)

            sqlusername = client.get_secret("sqlusr").value
            sqlpassword = client.get_secret("sqlpasswrd").value

            logging.debug(f'Retrieved the username {sqlusername} from Azure Key Vault')
            logging.info("Successfully retrieved secrets from Azure Key Vault")

        except Exception as ex:
            logging.exception("exception when attemping to get secrets from Azure Key Vault: {ex}")
            return func.HttpResponse("exception when attemping to get secrets from Azure Key Vault", status_code=500)

        try:
            logging.info('Connecting to SQL DB')

            server = 'tcp:ath-sqlsvr.database.windows.net'
            database = 'FreeDB'
            # indicate in the connection string from Azure portal. And check the local version
            driver = '{ODBC Driver 17 for SQL Server}'

            # get the connection string from portal: go to Database >> Under Settings: Connection strings >>> ODBC
            sql_conn = pyodbc.connect('DRIVER='+driver+';SERVER='+server +
                                  ',1433;DATABASE='+database+';UID='+sqlusername+';PWD=' + sqlpassword)
            
            logging.info("Successfully Connected to SQL DB")

        except Exception as ex:
            logging.exception("Exception when attempting to connect to SQL DB: {ex}")
            return func.HttpResponse("Exception when attempting to connect to SQL DB", status_code=500)


        try:
            logging.info('Fetching data from SQL')

            all_records_qry = "SELECT * FROM autos.inventory"
            car_models = []

            with sql_conn.cursor() as cursor:
                cursor.execute(all_records_qry)
                rows = cursor.fetchall()

                for row in rows:
                    logging.info(row)
                    car_models.append(row[2])
            
            logging.info(f"Successfully retrieved {str(len(rows))} car models")

            return func.HttpResponse(f"{car_models}")

        except Exception as ex:
            logging.exception("Exception when attempting to execute SQL query: {ex}")
            return func.HttpResponse("exception when attempting to execute SQL query", status_code=500)
        
  
    else:
        logging.info("This HTTP triggered function executed successfully. However you didn't pass a relevant request name.")
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. However you didn't pass a relevant request name.",
             status_code=200
        )