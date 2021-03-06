
from django.db import models


class User(models.Model):
    name = models.CharField(max_length=100,default='')
    password = models.CharField(max_length=100,default='')
    active_table_id = models.IntegerField(null=True, blank=True)
    def __unicode__(self):
        return "<User %s: %s>" % (self.id,self.name)


class Sample(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=100,default='')
    sha1 = models.CharField(max_length=100,default='') # hash of the file's content
    textfile = models.FileField(upload_to="text/")
    images = models.FileField(upload_to="images/")
    graph_active = models.BooleanField()
    def __unicode__(self):
        return "<[%s] %s, %s, %s>" % (self.id,self.name,self.sha1,self.textfile)


class Measurement(models.Model):
    user = models.ForeignKey(User)
    sample = models.ForeignKey(Sample)
    dose = models.FloatField()
    response = models.FloatField()
    experiment = models.IntegerField(default=-1)
    def __unicode__(self):
        return "<[%s] (%s, %s), s%s-e%s>" % (self.id,self.dose,self.response,self.sample.id,self.experiment)



# Make it so that deleting a Sample will delete the associated files.
# Receive the pre_delete signal and delete the file associated with the model instance.
from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

@receiver(post_delete, sender=Sample)
def mymodel_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    try: instance.textfile.delete(False)
    except: pass
    try: instance.images.delete(False)
    except: pass


#------------------------------------------------------#
# This code was written by Julien Delafontaine         #
# Bioinformatics and Biostatistics Core Facility, EPFL #
# http://bbcf.epfl.ch/                                 #
# webmaster.bbcf@epfl.ch                               #
#------------------------------------------------------#
