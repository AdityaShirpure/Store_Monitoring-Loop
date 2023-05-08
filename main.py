import asyncio     # Required to make async function
import uuid        # Required to generate unique IDs for reports
import pytz        # Required for working with timezones
import csv         # Required for generating CSV files
import uvicorn     # Required for running the FastAPI application
from database import MySql     # Required for interacting with the database
from datetime import datetime  # Required for working with timestamps
from fastapi import FastAPI, HTTPException  # Required for building the FastAPI application and handling HTTP exceptions
from fastapi.responses import FileResponse, JSONResponse  # Required for returning file and JSON responses

# This line of code initializes a new instance of the FastAPI framework
app = FastAPI()

#created an object of database
mydb = MySql.mydb

# array for all of my data
reports = []

#route for trigger_report
@app.get("/trigger_report")
async def trigger_report():
    # Getting the current timestamp
    cursor = mydb.cursor()
    cursor.execute("SELECT MAX(timestamp_utc) FROM store_status")
    max_timestamp = cursor.fetchone()[0]
    cursor.close()
   
    # Generating a random report ID
    report_id = str(uuid.uuid4())

    # Calling the report generating Function 
    asyncio.create_task(generate_report(report_id, max_timestamp)) 

    # Returning the report ID to the user
    return {"report_id": report_id}

# function for generate_report
async def generate_report(report_id,max_timestamp):
    # Initializing the report data dictionary
    report_data = {}
    
    # Getting the store status data from the database
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM store_monitoring.store_status")
    store_statuses = cursor.fetchall()
    cursor.close()

    
     # Getting the store status timezone from the database
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM store_monitoring.store_timezone")
    store_timezones = cursor.fetchall()
    cursor.close()

    # Looping through the store status data and calculate the report data for each store
    for store_status in store_statuses:
        # Extracting the relevant fields from the store status data
        store_id = store_status["store_id"]
        status = store_status["status"]
        timestamp_utc = store_status["timestamp_utc"]
        store_timezone = None
        for store_time in store_timezones:
            if store_time["store_id"] == store_id:
                store_timezone = pytz.timezone(store_time["timezone_str"])
                break

        # Converting the UTC timestamp to local time for the store
        if timestamp_utc is not None and store_timezone is not None:
            timestamp_local = timestamp_utc.astimezone(store_timezone)
        else:
            timestamp_local = None

        # Initializing the store's data in the report dictionary if it doesn't exist yet
        if store_id not in report_data:
            report_data[store_id] = {
                "uptime_last_hour": 0,
                "uptime_last_day": 0,
                "uptime_last_week": 0,
                "downtime_last_hour": 0,
                "downtime_last_day": 0,
                "downtime_last_week": 0
                }
        BUSINESS_START_HOUR = 9
        BUSINESS_END_HOUR = 17
        # Updating the store's data based on the current status
        if status == "active":
            # Checking if the current time is within business hours
            if timestamp_local is not None and timestamp_local.hour >= BUSINESS_START_HOUR and timestamp_local.hour < BUSINESS_END_HOUR:
                # Updating uptime counters
                report_data[store_id]["uptime_last_hour"] += 1
                report_data[store_id]["uptime_last_day"] += 1
                report_data[store_id]["uptime_last_week"] += 1
        else:
            # Checking if the current time is within business hours
            if timestamp_local is not None and timestamp_local.hour >= BUSINESS_START_HOUR and timestamp_local.hour < BUSINESS_END_HOUR:
                # Updating downtime counters
                report_data[store_id]["downtime_last_hour"] += 1
                report_data[store_id]["downtime_last_day"] += 1
                report_data[store_id]["downtime_last_week"] += 1


    # Converting the report data dictionary to a list of dictionaries
    report_list = []
    for store_id, data in report_data.items():
        # Converting uptime and downtime counters to minutes and hours, respectively
        data["uptime_last_hour"] *= 1
        data["uptime_last_day"] *= 60
        data["uptime_last_week"] *= 60
        data["downtime_last_hour"] *= 1
        data["downtime_last_day"] *= 60
        data["downtime_last_week"] *= 60

        # Appending the store data to the report list
        report_list.append({
            "store_id": store_id,
            "uptime_last_hour": data["uptime_last_hour"],
            "uptime_last_day": data["uptime_last_day"],
            "uptime_last_week": data["uptime_last_week"],
            "downtime_last_hour": data["downtime_last_hour"],
            "downtime_last_day": data["downtime_last_day"],
            "downtime_last_week": data["downtime_last_week"]
        })

    # Storing the report data in the global reports list
    reports.append({
        "report_id": report_id,
        "start_time": max_timestamp,
        "end_time": datetime.utcnow(),
        "data": report_list,
        "ready": True
    })
    return "Report generation Completed"

@app.get("/get_report")
async def get_report(report_id: str = None):
    # If report_id is None, return a list of all report IDs
    if report_id is None:
        return {"reports": [r["report_id"] for r in reports]}

    # Checking if the report exists
    report = next((r for r in reports if r["report_id"] == report_id), None)
   
    if not report:
        return "Invalid report ID"

    # Checking if the report is ready
    if not report["ready"]:
        return JSONResponse(content={"status": "Running"}, status_code=200)

    # Waiting for the report generation to complete
    while not report["ready"]:
        await asyncio.sleep(1)
        report = next((r for r in reports if r["report_id"] == report_id), None)

    # Generating the CSV file
    fieldnames = ["store_id", "uptime_last_hour", "downtime_last_hour", "uptime_last_day", "downtime_last_day", "uptime_last_week", "downtime_last_week"]

    filename = f"report_{report_id}.csv"
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in report["data"]:
            # Filtering out any fields that are not in the fieldnames list
            data_to_write = {k: v for k, v in data.items() if k in fieldnames}
            writer.writerow(data_to_write)

    # Returning the CSV file and the Completed message
    return JSONResponse(content={"filename": filename, "report_id": report_id, "status": "Complete"}, status_code=200)