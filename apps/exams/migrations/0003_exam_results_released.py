from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('exams', '0002_alter_question_question_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='results_released',
            field=models.BooleanField(
                default=False,
                help_text='Release results to students when immediate results are disabled.',
            ),
        ),
    ]
