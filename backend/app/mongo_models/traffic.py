from mongoengine import (
    Document,DateTimeField, IntField
)

class Traffic(Document):
    time = DateTimeField(required=True)
    carsIn = IntField(required=True)
    carsOut = IntField(required=True)
    motorcyclesIn = IntField(required=True)
    motorcyclesOut = IntField(required=True)
    busesIn = IntField(required=True)
    busesOut = IntField(required=True)
    trucksIn = IntField(required=True)
    trucksOut = IntField(required=True)