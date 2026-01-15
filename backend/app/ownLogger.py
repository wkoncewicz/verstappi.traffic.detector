from datetime import datetime, timezone
from mongo_models import logs
import logging
logger = logging.getLogger("app")

def saveLog(service,level,message,transactionId):
    if(level=='INFO'):
        logger.info(message,extra={'service':service,'transactionId':transactionId})
    elif(level=='ERROR'):
        logger.error(message,extra={'service':service,'transactionId':transactionId})
    elif(level=='WARNING'):
        logger.warning(message,extra={'service':service,'transactionId':transactionId})
    try:
        logs.Log(
            service=service,
            time = datetime.now(timezone.utc),
            message=message,
            transactionId=transactionId
        )
    except Exception as e:
        logger.error(f"An error occured while tryind to save log for transactionId {transactionId}")