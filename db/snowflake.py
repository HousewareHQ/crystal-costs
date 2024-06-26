
import os
import snowflake.connector as snow
import json

class Snowflake:
    def __init__(self, snowflake_account, snowflake_username, snowflake_password, snowflake_warehouse, snowflake_role):
        self.account = snowflake_account
        self.user = snowflake_username
        self.password = snowflake_password
        self.warehouse = snowflake_warehouse
        self.database = 'SNOWFLAKE'
        self.schema = 'ACCOUNT_USAGE'
        self.role = snowflake_role
        
        self.playground_database = "PREDICTION_ARCTIC_DB"
        self.playground_schema = "WAREHOUSE_METERING_PREDICTIONS"

    def get_snowflake_connection_url(self):
        s = f"snowflake://{self.user}:{self.password}@{self.account}/{self.database}/{self.schema}?warehouse={self.warehouse}&role={self.role}"
        return s
    
    def get_snowflake_connection(self, playground=False):
        return snow.connect(
            user=self.user,
            password=self.password,
            account=self.account,
            warehouse=self.warehouse,
            database=self.playground_database if playground else self.database,
            schema=self.playground_schema if playground else self.schema
        )
    
    def sf_forecast_call(self, timestamp_column, value_column, warehouse_column, warehouse_name, days):
        try:
            conn = self.get_snowflake_connection(playground=True)
            model_name = self.__get_model_name()
            with conn.cursor() as cur: 
                create_model_query = self.__get_model_create_sql(model_name, timestamp_column, value_column, warehouse_column, warehouse_name)
                print(create_model_query)
                inference_query = f"CALL {model_name}!FORECAST(FORECASTING_PERIODS => {days});"
                drop_model = f"DROP SNOWFLAKE.ML.FORECAST {model_name}"

                _ = cur.execute(create_model_query)
                data = cur.execute(inference_query).fetchall()
                cleaned_data = []
                if warehouse_name:
                    warehouse_name = warehouse_name.lower()
                    for row in data:
                        if row[0].lower() == f'"{warehouse_name}"':
                            cleaned_data.append(data)
                else:
                    cleaned_data = data
                _ = cur.execute(drop_model)
                return cleaned_data
        except Exception as e:
            print("Issue with quering data", e)
        finally:
            conn.close()

    def __get_model_create_sql(self, model_name, timestamp_column, value_column, warehouse_column, warehouse_name) -> str:
        # if warehouse_name:
        return f"""
            CREATE OR REPLACE SNOWFLAKE.ML.FORECAST {model_name}(
                INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'credit_usage_view'),
                SERIES_COLNAME => '{warehouse_column}',
                TIMESTAMP_COLNAME => '{timestamp_column}',
                TARGET_COLNAME => '{value_column}'
            )
        """
        
    def __get_model_name(self) -> str:
        return "credit_usage_model"
    
    def call_arctic_complete(self, messages):
        conn = self.get_snowflake_connection()
        with conn.cursor() as cur:
            sql = "SELECT snowflake.cortex.complete('snowflake-arctic', " + str(messages) +", {}) AS llm_response"
          
            cur.execute(sql)
            data = json.loads(cur.fetchall()[0][0])
        conn.close()

        return data.get("choices", [{}])[0].get("messages", "")