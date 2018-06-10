# coding: utf8
from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.cab, name="index"),

    # url(r'^buy/$', views.cab2, name="buy"),
    url(r'^buy/(?P<username>.+)/$', views.cab2, name="buy"),

    # url(r'^active_trades/$', views.cab3, name="active_trades"),
    url(r'^active_trades/(?P<username>.+)/$', views.cab3, name="active_trades"),
    
    # url(r'^pending/$', views.cab4, name="pending"),
    url(r'^pending/(?P<username>.+)/$', views.cab4, name="pending"),

    url(r'^portfolio/(?P<username>.+)/$', views.cab5, name="portfolio"),

    url(r'^balance/(?P<username>.+)/$', views.cab6, name="balance"),

    url(r'^ext/(.+)/$', views.cab_ext),
    url(r'^history/$', views.history, name="history"),
    url(r'^buyShares/$', views.buyShares, name='buyShares'),
    url(r'^sellShares/$', views.sellShare, name='sellShares'),
    url(r'^dataChart/$', views.dataChart, name='dataChart'),
    url(r'^dataNews/$', views.dataNews, name='dataNews'),
    url(r'^dataInformations/$', views.dataInformations, name='dataInformations'),
    url(r'^FAQ/$', views.FAQ, name='FAQ'),
    url(r'^dataCompanyPrice/$', views.dataCompanyPrice, name='dataCompanyPrice'),
    url(r'^dataChartTwo/$', views.dataChartTwo, name='dataChartTwo'),
    url(r'^resetPassword/$', views.resetPassword, name='resetPassword'),
    url(r'^editTiket/(?P<pk>.+)/$', views.editTiket, name='editTiket'),
    url(r'^openTiket/(?P<pk>.+)/$', views.openTiket, name='openTiket'),
    url(r'^dataChartTwoOneLement/$', views.lastShapePrice, name='lastShapePrice')


]
