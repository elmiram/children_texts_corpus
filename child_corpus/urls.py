#  -- coding: utf8 --

from django.conf.urls import patterns, include, url
from Corpus.views import Index, Search, Statistics, PopUp
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from news.views import NewsView, SectionView
from annotator.admin import learner_admin

urlpatterns = patterns('',
    url(r'^admin/', include(learner_admin.urls)),
    url(r'^(help)/$', Index.as_view(), name='main.static'),
    url(r'^news/$', NewsView.as_view(), name='news'),
    url(r'^search/$', Search.as_view(), name='main.search'),
    url(r'^search/(gramsel|lex|errsel)$', PopUp.as_view(), name='popup'),
    url(r'^stats/$', Statistics.as_view(), name='main.stats'),
    url(r'^document-annotations', include('annotator.urls')),
    (r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^$', SectionView.as_view(), name='start_page'),
    )

urlpatterns += staticfiles_urlpatterns()