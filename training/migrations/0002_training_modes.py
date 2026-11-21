from django.db import migrations


def create_modes(apps, schema_editor):
    TrainingMode = apps.get_model("training", "TrainingMode")
    TrainingMode.objects.bulk_create([
        TrainingMode(
            slug="reaction",
            name="Швидкість реакції",
            description="Дочекайтеся зеленого сигналу та натисніть якомога швидше. Дізнайтеся свій час реакції в мілісекундах.",
        ),
        TrainingMode(
            slug="concentration",
            name="Концентрація уваги",
            description="Реагуйте на зелені сигнали та пропускайте червоні. Утримуйте увагу протягом серії з десяти сигналів.",
        ),
    ])


def remove_modes(apps, schema_editor):
    TrainingMode = apps.get_model("training", "TrainingMode")
    TrainingMode.objects.filter(slug__in=["reaction", "concentration"]).delete()


class Migration(migrations.Migration):
    dependencies = [("training", "0001_initial")]
    operations = [migrations.RunPython(create_modes, remove_modes)]
