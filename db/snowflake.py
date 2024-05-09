
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

    def get_snowflake_connection_url(self):
        return f"snowflake://{self.user}:{self.password}@{self.account}/{self.database}/{self.schema}?warehouse={self.warehouse}&role={self.role}"
    
    def get_snowflake_connection(self):
        return snow.connect(
            user=self.user,
            password=self.password,
            account=self.account,
            warehouse=self.warehouse,
            database=self.database,
            schema=self.schema
        )
    
    def sf_forecast_call(self, data):
        pass