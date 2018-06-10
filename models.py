# coding: utf8
from django.db import models
from Users.models import User, Company


class news(models.Model):
    head = models.CharField(u'Your news', max_length=100)
    text = models.TextField(default="")
    company = models.ForeignKey(Company)
    date = models.DateTimeField(auto_now_add=True)
    public = models.BooleanField(default=False)


class historyBuy(models.Model):
    user = models.ForeignKey(User)
    count = models.IntegerField(default=0)
    company = models.ForeignKey(Company)
    date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=20, decimal_places=2, default=0.1)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=2, default=0.1, blank=True)
    take_profit = models.DecimalField(max_digits=20, decimal_places=2, default=0.1, blank=True)


class shapePrice(models.Model):
    company = models.ForeignKey(Company)
    date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    priceTrans = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)