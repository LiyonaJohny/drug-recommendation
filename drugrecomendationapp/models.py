from django.db import models

# NOTE: These tables are created and populated by drug_recomdendation.sql, not by
# Django migrations. `managed = False` tells Django to leave the schema alone
# (no makemigrations/migrate for them) while still allowing ORM reads and writes
# such as mmodel().save() in the medicine-upload view.

class mmodel(models.Model):
    name=models.CharField(max_length=100)
    used=models.CharField(max_length=100)
    mg=models.CharField(max_length=100)
    dosage=models.CharField(max_length=100)
    cmp=models.CharField(max_length=100)
    effects=models.CharField(max_length=100)
    pres=models.CharField(max_length=100)
    pack=models.CharField(max_length=100)
    image=models.FileField(upload_to="media")

    class Meta:
        db_table = "med_details"
        managed = False


class Feedback(models.Model):
    fid = models.AutoField(primary_key=True)
    uid = models.IntegerField()
    feedback = models.CharField(max_length=100)
    fdate = models.DateField()

    class Meta:
        db_table = "feedback"
        managed = False
