from mongoengine import connect
from mongo_models import traffic, logs
from datetime import datetime, timezone
import logging
import os
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

if not logger.handlers:
    h = logging.StreamHandler()
    h.setLevel(logging.INFO)
    h.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(h)

logger.propagate = False
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

service = {
    'name': "[MONGO]",
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


def saveLog(service,level,message,transactionId):
    newMessage = f'{service} {level} {message} transactionId: {transactionId}'
    if(level=='INFO'):
        logger.info(newMessage,extra={'service':service,'transactionId':transactionId})
    elif(level=='ERROR'):
        logger.error(newMessage,extra={'service':service,'transactionId':transactionId})
    elif(level=='WARNING'):
        logger.warning(newMessage,extra={'service':service,'transactionId':transactionId})
    try:
        log = logs.Logs(
            service=service,
            time = datetime.now(timezone.utc),
            type=level,
            message=message,
            transactionId=transactionId
        )
        log.save()
    except Exception as e:
        logger.error(f"An error {e} occured while trying to save log for transactionId: {transactionId}")