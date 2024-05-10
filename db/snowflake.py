
import os
import snowflake.connector as snow



class Snowflake:
    def __init__(self):
        self.account = os.environ["SNOWFLAKE_ACCOUNT"]
        self.user = os.environ["SNOWFLAKE_USERNAME"]
        self.password = os.environ["SNOWFLAKE_PASSWORD"]
        self.warehouse = os.environ["SNOWFLAKE_WAREHOUSE"]
        self.database = os.environ["SNOWFLAKE_DATABASE"]
        self.schema = os.environ["SNOWFLAKE_SCHEMA"]
        self.role = os.environ["SNOWFLAKE_ROLE"]
        
        self.playground_database = "PROD_HOUSEWARE_DEMOS"
        self.playground_schema = "PRODUCT_ANALYTICS_FRIDAY_DEMO"

    def get_snowflake_connection_url(self):
        return f"snowflake://{self.user}:{self.password}@{self.account}/{self.database}/{self.schema}?warehouse={self.warehouse}&role={self.role}"
    
    def get_snowflake_connection(self, playground=False):
        return snow.connect(
            user=self.user,
            password=self.password,
            account=self.account,
            warehouse=self.warehouse,
            database=self.playground_database if playground else self.database,
            schema=self.playground_schema if playground else self.schema
        )
    
    def sf_forecast_call(self, timestamp_column, value_column, days):
        try:
            conn = self.get_snowflake_connection(playground=True)
            model_name = self.__get_model_name()
            with conn.cursor() as cur: 
                create_model_query = f"""
                    CREATE OR REPLACE SNOWFLAKE.ML.FORECAST {model_name}(
                        INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'credit_usage_view'),
                        TIMESTAMP_COLNAME => '{timestamp_column}',
                        TARGET_COLNAME => '{value_column}'
                    )
                """
                inference_query = f"CALL {model_name}!FORECAST(FORECASTING_PERIODS => {days});"
                drop_model = f"DROP SNOWFLAKE.ML.FORECAST {model_name}"

                _ = cur.execute(create_model_query)
                data = cur.execute(inference_query).fetchall()
                _ = cur.execute(drop_model)
                return data
        except Exception as e:
            print("Issue with quering data", e)
        finally:
            conn.close()

    def __get_model_name(self) -> str:
        return "credit_usage_model_raj"