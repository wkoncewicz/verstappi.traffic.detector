from mongoengine import (
    Document, EmbeddedDocument,DateTimeField, EmbeddedDocumentField, IntField
)
class Vehicle(EmbeddedDocument):
    vehicles_in = IntField(required=True)
    vehicles_out = IntField(required=True)

class Traffic(Document):
    time = DateTimeField(required=True)
    cars = EmbeddedDocumentField(Vehicle,required=True)
    motorcycles = EmbeddedDocumentField(Vehicle,required=True)
    buses = EmbeddedDocumentField(Vehicle,required=True)
    trucks = EmbeddedDocumentField(Vehicle,required=True)
