# -*- coding=utf-8 -*-

from django.shortcuts import render_to_response
from django.views.generic import View
from django.template import *
from news.models import Article, Section


import re
rePage = re.compile(u'&page=\\d+', flags=re.U)


class NewsView(View):

    def get(self, request):
        art_list = Article.objects.order_by('-date')
        page = 'news.html'
        return render_to_response(page, {'articles': art_list}, context_instance=RequestContext(request))


class SectionView(View):
    def get(self, request):
        section_list = Section.objects.order_by('number')
        page = 'start.html'
        return render_to_response(page, {'sections': section_list}, context_instance=RequestContext(request))

