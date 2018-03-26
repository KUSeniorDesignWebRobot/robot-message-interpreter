import uuid
import logging

class Report():

    def __init__(self, reportMessageGenerator):
        self.reportMessageGenerator = reportMessageGenerator
        self.sensor_id = None
        self.ttl = None
        self.value = None
        self.source = None
        self.kwargs = {}

    def build(self, sensor_id, ttl, value, source, **kwargs):
        self.sensor_id = sensor_id
        self.ttl = ttl
        self.value = value
        self.source = source
        self.kwargs = kwargs

    def send(self):
        self.reportMessageGenerator.enqueue(self)
        
    def asDict(self):
        """
        Returns a dict representation of this Report for insertion into a ReportMessage
        """
        return {
            "sensor_id": self.sensor_id,
            "ttl": self.ttl,
            "value": self.value,
            "source": self.source,
            **self.kwargs
        }
    
    def __str__(self):
        return str(self.asDict())

