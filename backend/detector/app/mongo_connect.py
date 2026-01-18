from mongoengine import connect
from mongo_models import traffic 
from datetime import datetime
import os

host_env = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
auth_source = "admin"
mongo_host = f"mongodb://{host_env}:27017"

def mongo_connect():
    try:
        connect(
            db=host_env,
            host=mongo_host,
            username=db_user,
            password=db_password,
            authentication_source=auth_source
        )
        print("Connected to MongoDB")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

def saveToDataBase(trafficObject):
    try:
        data = traffic.Traffic(
            time= trafficObject['timeStamp'],
            cars= traffic.Vehicle(vehicles_in=trafficObject['carIn'],vehicles_out=trafficObject['carOut']),
            motorcycles= traffic.Vehicle(vehicles_in=trafficObject['motorcycleIn'],vehicles_out=trafficObject['motorcycleOut']),
            buses= traffic.Vehicle(vehicles_in=trafficObject['busIn'],vehicles_out=trafficObject['busOut']),
            trucks= traffic.Vehicle(vehicles_in=trafficObject['truckIn'],vehicles_out=trafficObject['truckOut'])
        )

        data.save() 
    except Exception as e:
        print(f"Error saving to database: {e}")
        return None
        