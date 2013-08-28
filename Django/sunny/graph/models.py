from django.db import models

class Sample(models.Model):
    name = models.CharField(max_length=100,default='')
    sha1 = models.CharField(max_length=20,default='') # hash of the file's content

    def __unicode__(self):
        return "[%s] %s, %s" % (self.id,self.name,self.sha1)

class Measurement(models.Model):
    sample = models.ForeignKey(Sample)
    dose = models.FloatField()
    response = models.FloatField()
    experiment = models.IntegerField(default=-1)

    def __unicode__(self):
        return "[%s] (%s, %s), exp.%s" % (self.id,self.dose,self.response,self.experiment)

