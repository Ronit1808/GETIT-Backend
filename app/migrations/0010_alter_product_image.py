# Generated by Django 5.1.3 on 2024-12-10 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_order_payment_method_order_shipping_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.ImageField(upload_to='img/'),
        ),
    ]