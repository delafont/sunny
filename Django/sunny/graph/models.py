from django.db import models

class Sample(models.Model):
    name = models.CharField(max_length=100,default='')

    def __unicode__(self):
        return self.name

class Measurement(models.Model):
    sample = models.ForeignKey(Sample)
    dose = models.FloatField()
    response = models.FloatField()
    experiment = models.IntegerField(default=-1)

    def __unicode__(self):
        return "(%s,%s)" % (self.dose,self.response)

