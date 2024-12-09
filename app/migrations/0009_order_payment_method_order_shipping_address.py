# Generated by Django 5.1.3 on 2024-12-07 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_order_razorpay_order_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.TextField(default='razorpay'),
        ),
        migrations.AddField(
            model_name='order',
            name='shipping_address',
            field=models.TextField(default=''),
        ),
    ]
