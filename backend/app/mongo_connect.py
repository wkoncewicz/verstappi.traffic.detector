from mongoengine import connect
from mongo_models import traffic
from datetime import datetime, timezone
from ownLogger import saveLog
import os

# Resolve Mongo connection settings from environment (with sensible defaults)
host_env = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
auth_source = "admin"
mongo_host = f"mongodb://{host_env}:27017"

connect(
    db=host_env,
    host=mongo_host,
    username=db_user,
    password=db_password,
    authentication_source=auth_source
)

service = {
    'name': "MONGO",
    'info': "INFO",
    'error' : "ERROR",
    'warning': "WARNING"
}

def getTime():
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return time

def saveToDataBase(amount,transId):
    try:
        data = traffic.TrafficWithTimeStamp(time=getTime(),amount=amount)
        data.save()
        saveLog(service['name'],service['info'],"saved data to database",transId)
    except Exception as e:
        saveLog(service['name'],service['error'],str(e),transId)
        
def readFromDataBase(transId):
    try:
        data = traffic.TrafficWithTimeStamp.objects()
        saveLog(service['name'],service['info'],"granting database data",transId)
        return data
    except Exception as e:
        saveLog(service['name'],service['error'],str(e),transId)