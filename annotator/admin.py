#  -- coding: utf8 --

import os
from django.contrib import admin
from annotator.models import Document, Annotation, Morphology
from news.models import Article, Section
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin


class LearnerCorpusAdminSite(AdminSite):
    site_header = 'Child Corpus'
    site_title = 'Admin'
    index_title = 'Corpus'


class ArticleAdmin(admin.ModelAdmin):
    fields = ['date', 'text_eng', 'text_rus']
    list_display = ('date', 'text_eng', 'text_rus', 'created')


class SectionAdmin(admin.ModelAdmin):
    fields = ['number', 'issubheader', 'header_eng', 'text_eng', 'header_rus', 'text_rus']
    list_display = ('number', 'header_eng', 'text_eng', 'header_rus', 'text_rus')


class ExpAdmin(admin.ModelAdmin):
    fields = ['number', 'issubheader', 'header_eng', 'text_eng', 'header_rus', 'text_rus']
    list_display = ('number', 'header_eng', 'text_eng', 'header_rus', 'text_rus')


class DocumentAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['owner', 'title', 'body', 'filename', 'date', 'audio_file', 'image_file', 'transcript', 'type_of_task']}),
        ('Author', {'fields': [('author', 'gender', 'city'), ('birth', 'grade')]}),
        ('Autocompletion', {'fields': [('annotated', 'checked')], 'classes': [('collapse')]}),
    ]

    list_display = ('title', 'author', 'gender', 'grade', 'city', 'date', 'audio_file_player', 'image_img', 'annotated', 'checked', 'created')
    list_filter = ['gender', 'city', 'grade']

    actions = ['custom_delete_selected']

    def custom_delete_selected(self, request, queryset):
        for i in queryset:
            if i.audio_file:
                if os.path.exists(i.audio_file.path):
                    os.remove(i.audio_file.path)
            if i.image_file:
                if os.path.exists(i.image_file.path):
                    os.remove(i.image_file.path)
            i.delete()
        self.message_user(request, "Successfully deleted.")

    custom_delete_selected.short_description = "Delete selected items"

    def get_actions(self, request):
        actions = super(DocumentAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions


class AnnotationAdmin(admin.ModelAdmin):
    readonly_fields = ('annotated_doc',)
    list_display = ('annotated_doc', 'tag', 'owner', 'speech_therapist', 'native_language', 'updated', 'created')

    def annotated_doc(self, instance):
        return instance.document.doc_id.title


class MorphAdmin(admin.ModelAdmin):
    list_display = ('token', 'lem', 'lex', 'gram')


class MorphInline(admin.TabularInline):
    model = Morphology
    extra = 0


class TokenAdmin(admin.ModelAdmin):
    readonly_fields = ('sent_num',)
    fieldsets = [
        (None,               {'fields': ['token', 'doc', 'sent']}),
        ('Token data', {'fields': [('num', 'punctl', 'punctr', 'sent_pos')]}),
    ]

    list_display = ('token', 'sent_num', 'num', 'doc')
    inlines = [MorphInline]

    def sent_num(self, instance):
        return instance.sent.num


learner_admin = LearnerCorpusAdminSite(name='admin')
learner_admin.register(Document, DocumentAdmin)
learner_admin.register(Annotation, AnnotationAdmin)
learner_admin.register(Article, ArticleAdmin)
learner_admin.register(Section, SectionAdmin)
learner_admin.register(User, UserAdmin)
learner_admin.register(Group, GroupAdmin)
