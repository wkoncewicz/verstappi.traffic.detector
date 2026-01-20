
from datetime import datetime


day = datetime(2000, 1, 1)
obj = {
    "timeStamp": day.isoformat()
}

print(obj["timeStamp"][5:7])