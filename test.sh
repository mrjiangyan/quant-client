influx config create --config-name influx \
  --host-url http://localhost:8086 \
  --org touchbiz \
  --token 123456 \
  --active

influx setup --username influx --password 12345678 --org touchbiz --bucket stock-bucket-day --force



influx delete --bucket "stock-bucket-day" --start '1970-01-01T00:00:00Z' --stop "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" --predicate '_measurement="stock_k_line_5m"' --host http://localhost:8086 --token Ima4zi8DjZ7_6P5in31lTgEX8dJL61CBBmj3G5YxGFSQy5_7YJQMo-vBtgivaXlgAtu8kyQX4WaeCCUwhUYAHA==

influx delete --bucket "stock-bucket-day" --start '1970-01-01T00:00:00Z' --stop "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" --predicate '_measurement="stock_k_line_15m"' --host http://localhost:8086 --token Ima4zi8DjZ7_6P5in31lTgEX8dJL61CBBmj3G5YxGFSQy5_7YJQMo-vBtgivaXlgAtu8kyQX4WaeCCUwhUYAHA==


influx delete --bucket "stock-bucket-day" --start '1970-01-01T00:00:00Z' --stop "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" --predicate '_measurement="stock_k_line_1m"' --host http://localhost:8086 --token Ima4zi8DjZ7_6P5in31lTgEX8dJL61CBBmj3G5YxGFSQy5_7YJQMo-vBtgivaXlgAtu8kyQX4WaeCCUwhUYAHA==


