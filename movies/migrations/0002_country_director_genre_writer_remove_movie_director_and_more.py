# Generated by Django 4.0.6 on 2024-09-28 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Director',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('staff_id', models.IntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Writer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('staff_id', models.IntegerField(unique=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='movie',
            name='director',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='genre',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='url',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='users_dislike',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='users_watched',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='users_watchlist',
        ),
        migrations.AddField(
            model_name='movie',
            name='countries',
            field=models.ManyToManyField(related_name='movies_country', to='movies.country'),
        ),
        migrations.AddField(
            model_name='movie',
            name='directors',
            field=models.ManyToManyField(related_name='movies_director', to='movies.director'),
        ),
        migrations.AddField(
            model_name='movie',
            name='genres',
            field=models.ManyToManyField(related_name='movies_genre', to='movies.genre'),
        ),
        migrations.AddField(
            model_name='movie',
            name='writers',
            field=models.ManyToManyField(related_name='movies_writer', to='movies.writer'),
        ),
    ]
