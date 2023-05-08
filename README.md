# Store_Monitoring-Loop

The code provided is a FastAPI application that generates reports based on data stored in a MySQL database. The application has two routes:

/trigger_report: This route generates a new report by calling the generate_report function as an asynchronous task. The function selects data from two tables in the database and calculates statistics for each store, based on their status and timezone. The resulting report data is stored in a global list.

/get_report: This route takes a report_id parameter and returns the report data associated with that ID, if available. If the report data is not yet available, the function raises an HTTPException with a 404 status code.

The application also imports several Python modules:

asyncio: Used for creating an asynchronous task that runs the generate_report function.
uuid: Used for generating a unique ID for each report.
pytz: Used for working with timezones in the generate_report function.
csv: Used for generating CSV files in the export_report function (which is not shown in the code provided).
uvicorn: Used for running the FastAPI application.
database: Used for interacting with the MySQL database.
