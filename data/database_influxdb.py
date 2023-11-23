from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
import pandas as pd

class MyInfluxDBClient:
    def __init__(self):
        self.client = InfluxDBClient.from_config_file("data/config.ini")
        self.write_api = self.client.write_api(write_options= SYNCHRONOUS)
        self.query_api = self.client.query_api()
       
        #influx delete --bucket "stock-bucket-day" --start '1970-01-01T00:00:00Z' --stop "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" --predicate '_measurement="stock_k_line_day"' --host http://localhost:8086 --token Ima4zi8DjZ7_6P5in31lTgEX8dJL61CBBmj3G5YxGFSQy5_7YJQMo-vBtgivaXlgAtu8kyQX4WaeCCUwhUYAHA==
        #influx delete --bucket "stock-bucket-day" --start '1970-01-01T00:00:00Z' --stop "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" --predicate '_measurement="my_measurement"' --host http://localhost:8086 --token Ima4zi8DjZ7_6P5in31lTgEX8dJL61CBBmj3G5YxGFSQy5_7YJQMo-vBtgivaXlgAtu8kyQX4WaeCCUwhUYAHA==


   

    def write_data(self, bucket_name, data_points):
        self.write_api.write(bucket=bucket_name, record=data_points)
      
    def query(self, query):
        result = self.query_api.query(query)
        return result
    
    def query_data_frame(self, query) -> pd.DataFrame:
        result = self.query_api.query_data_frame(query)
        return result
    
    def check_data_existence(self, bucket_name, measurement, tags, start_time, end_time):
        flux_query = f'''from(bucket: "{bucket_name}")
            |> range(start: {start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_time.strftime('%Y-%m-%dT%H:%M:%SZ')})
            |> filter(fn: (r) => r["_measurement"] == "{measurement}")'''

        for tag_name, tag_values in tags.items():
             flux_query += f'\n    |> filter(fn: (r) => r["{tag_name}"] == "{tag_values}")'
               
        flux_query += '\n    |> last()'
        # Execute the query
        result = self.query(flux_query)

        # Check if any results were returned
        return len(result) > 0

