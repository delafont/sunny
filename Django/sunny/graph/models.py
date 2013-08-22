from django.db import models

class Measurement(models.Model):
    def __unicode__(self):
        return "(%s,%s)" % (self.dose,self.response)
    sample = models.CharField(max_length=100,default='')
    dose = models.FloatField()
    response = models.FloatField()
    experiment = models.IntegerField(default=-1)

