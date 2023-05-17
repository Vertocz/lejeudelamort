# Generated by Django 4.1.7 on 2023-05-16 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('JeuDeLaMort', '0003_ligue_alter_candidat_wiki_id_pari_unique_ligue_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pari_unique',
            old_name='candidat_wiki_id',
            new_name='wiki_id',
        ),
        migrations.RemoveField(
            model_name='ligue',
            name='candidats_uniques',
        ),
        migrations.AlterField(
            model_name='ligue',
            name='description',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='ligue',
            name='nom',
            field=models.CharField(max_length=60),
        ),
    ]
