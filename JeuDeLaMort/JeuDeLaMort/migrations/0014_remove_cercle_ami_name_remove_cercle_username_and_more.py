# Generated by Django 4.1.7 on 2023-08-11 19:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('JeuDeLaMort', '0013_cercle_ami_name_cercle_username_pari_candidat_nom_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cercle',
            name='ami_name',
        ),
        migrations.RemoveField(
            model_name='cercle',
            name='username',
        ),
        migrations.RemoveField(
            model_name='pari',
            name='candidat_nom',
        ),
        migrations.RemoveField(
            model_name='pari',
            name='user_id',
        ),
        migrations.RemoveField(
            model_name='pari',
            name='username',
        ),
        migrations.RemoveField(
            model_name='pari',
            name='wiki_id',
        ),
    ]
