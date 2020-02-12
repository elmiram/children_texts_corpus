#  -- coding: utf8 --

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from audiofield.models import AudioFile
from audiofield.fields import AudioField

import json
from annotator.utils import *
import re

bold_regex = re.compile('/b\\[(\\d+)\\]')
span_regex = re.compile('span\\[(\\d+)\\]')


class Document(models.Model):
    """A document being annotated"""
    owner = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    title = models.CharField(max_length=64, db_index=True, null=True, blank=True)

    body = models.TextField(help_text=_("Paste the text here."), verbose_name=_('text'))  # HTML
    # todo probably should delete this field and create a special form in admin

    author = models.CharField(max_length=50, help_text=_("Enter author's first and/or  second name."), verbose_name=_('author'))
    filename = models.CharField(max_length=1000, help_text=_("Enter the name of the file from which the text is taken."), verbose_name=_('file name'))

    audio_file = AudioField(db_index=True, null=True, upload_to='audio/', blank=True,
                            ext_whitelist=(".mp3", ".wav", ".ogg"),
                            help_text="Allowed types - .mp3, .wav, .ogg")

    image_file = models.ImageField(upload_to='images/', null=True, blank=True, help_text="Allowed types - .jpg .png")

    transcript = models.TextField(help_text=_("Enter transcript."), verbose_name=_('transcript'))

    # optional fields - need them for meta in CoRST
    date = models.DateField(db_index=True, null=True, blank=True, help_text=_("When the work on the text started, e.g. 2014."), verbose_name=_('date'))
    gender = models.CharField(max_length=1, null=True, blank=True, choices=((u'ж', _(u'женский')), (u'м', _(u'мужской'))), db_index=True, verbose_name=_('gender'))
    type_of_task = models.CharField(max_length=50, null=True, blank=True, db_index=True,  verbose_name=_('type_of_task'))
    birth = models.IntegerField(null=True, blank=True, help_text=_("Year of the author's birth"), verbose_name=_('birth'))
    grade = models.IntegerField(null=True, blank=True,verbose_name=_('grade'))
    city = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('city'))

    # needed for general corpus statictics
    words = models.IntegerField(editable=False, null=True, blank=True, verbose_name=_('number of words'))
    sentences = models.IntegerField(editable=False, null=True, blank=True, verbose_name=_('number of sentences'))

    # needed for annotation statistics
    annotated = models.BooleanField(default=False, verbose_name=_('text is annotated'))
    checked = models.BooleanField(default=False, verbose_name=_('text is checked'))

    def __unicode__(self):
        return self.title

    def save(self, **kwargs):
        handle_sents = False
        if self.id is None:
            handle_sents = True
        super(Document, self).save()
        # todo how to close body change after a Document has been created?
        # we don't want people to change the texts after it has been parsed and loaded to the DB
        # but we want them to be able to edit meta
        if handle_sents:
            pass
            self.handle_sentences()

    def handle_sentences(self):
        self.words, text = mystem(self.body)
        self.sentences = len(text)
        super(Document, self).save()
        for sent_id in range(len(text)):
            sent, created = Sentence.objects.get_or_create(text=text[sent_id].text, doc_id=self, num=sent_id+1)
            words = text[sent_id].words
            stagged = []
            for i_word in range(len(words)):
                sent_pos = ''
                if i_word == 0: sent_pos = 'bos'
                elif i_word == len(words) - 1: sent_pos = 'eos'
                token, created = Token.objects.get_or_create(doc=self, sent=sent, num=i_word+1,
                                                             sent_pos=sent_pos,
                                                             token=words[i_word].wf,
                                                             punctr=words[i_word].pr,
                                                             punctl=words[i_word].pl)
                analyses = words[i_word].anas
                all_ana = words[i_word].tooltip
                for ana in analyses:
                    lem = ana[0]
                    bastard = False
                    if 'qual="' in lem:
                        lem = lem.split('"')[0]
                        bastard = True
                    lex, gram = ana[1].split('=')
                    if ',' in lex:
                        lex = lex.split(',')
                        gram = ','.join(lex[1:]) + ',' + gram
                        lex = lex[0]
                    if bastard:
                        gram = 'bastard,' + gram
                    Morphology.objects.get_or_create(token=token, lem=lem,
                                                     lex=lex, gram=gram)
                word = ' <span class="token" title="' + all_ana + '">' + \
                       token.punctl + token.token + token.punctr + '</span> '
                # todo rethink this piece
                # Tim says storing html is fine, since you never change it later and they do it in EANC, for example
                # but still, there must be a better implementation - absolutely not urgent
                stagged.append(word)
            sent.tagged = ''.join(stagged)
            sent.save()

    def audio_file_player(self):
        """audio player tag for admin"""
        if self.audio_file:
            file_url = os.path.join(settings.MEDIA_URL, str(self.audio_file))
            player_string = '<audio src="%s" controls>Your browser does not support the audio element.</audio>' % (
                file_url
            )
            return player_string

    audio_file_player.allow_tags = True
    audio_file_player.short_description = 'Audio file'

    def image_img(self):
        url = os.path.join(settings.MEDIA_URL, str(self.image_file))
        if self.image_file:
            return '<img src="{}" width="100%" onclick="location=\'{}\'"/>'.format(url, url)
        else:
            return '(none)'

    image_img.allow_tags = True
    image_img.short_description = 'Image'

    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')


class Sentence(models.Model):
    text = models.TextField()
    doc_id = models.ForeignKey(Document)
    num = models.IntegerField()
    tagged = models.TextField()  # stores the html-piece

    def __unicode__(self):
        return self.text

    class Meta:
        verbose_name = _('sentence')
        verbose_name_plural = _('sentences')


class Annotation(models.Model):
    # taken from Django-Annotator-Store
    owner = models.ForeignKey(User, db_index=True, blank=True, null=True)
    document = models.ForeignKey(Sentence, db_index=True)
    guid = models.CharField(max_length=64, unique=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)
    data = models.TextField()  # all other annotation data as JSON
    speech_therapist = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    native_language = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    tag = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    start = models.IntegerField(blank=True, null=True)
    end = models.IntegerField(blank=True, null=True)

    def set_guid(self):
        self.guid = str(uuid.uuid4())

    def save(self, **kwargs):
        if not self.owner:
            return
        super(Annotation, self).save()

    def can_edit(self, user):
        # if self.owner and self.owner != user and (not user or not user.has_perm('annotator.change_annotation')):
        #     return False
        if not user or not user.has_perm('annotator.change_annotation'):
            return False
        return True

    def as_json(self, user=None):
        d = {"id": self.guid,
             "document": self.document_id,
             "created": self.created.isoformat(),
             "updated": self.updated.isoformat(),
             "readonly": not self.can_edit(user),
             }

        d.update(json.loads(self.data))

        return d

    def check_fields(self, start, end, startOffset, endOffset, quote, sent):
        q_enc = quote.encode('utf-8')
        q_len = len(q_enc.split(' '))
        if start != '':
            start = bold_regex.sub('', start)
            self.start = int(span_regex.search(start).group(1))
            if end == "":
                end = '/span['+str(self.start+q_len-1)+']'
                endOffset = len(q_enc.split(' ')[-1].decode('utf-8').strip(' ,:;!?.'))
            else:
                end = bold_regex.sub('', end)
            self.end = int(span_regex.search(end).group(1))
        else:
            if end != '':
                end = bold_regex.sub('', end)
                self.end = int(span_regex.search(end).group(1))
                start = '/span['+str(self.end-q_len+1)+']'
                startOffset = 0
                self.start = int(span_regex.search(start).group(1))
            else:
                sent = Sentence.objects.get(id=sent).text.encode('utf-8')
                s = re.split(q_enc, sent)
                part = len(re.split(q_enc, sent)[0].strip().split(' '))
                self.start = part + 1
                self.end = part + q_len
                start = '/span['+str(self.start)+']'
                startOffset = 0
                end = '/span['+str(self.end)+']'
                endOffset = len(q_enc.split(' ')[-1].decode('utf-8').strip(' ,:;!?.'))
        return start, end, startOffset, endOffset

    def update_from_json(self, new_data):
        d = json.loads(self.data)

        for k, v in new_data.items():  # Skip special fields that we maintain and are not editable.
            if k in ('document', 'id', 'created', 'updated', 'readonly'):
                continue

                # Put other fields into the data object.
            d[k] = v

        quote = d['quote']
        start, end, startOffset, endOffset = d["ranges"][0]["start"], d["ranges"][0]["end"], d["ranges"][0]["startOffset"], d["ranges"][0]["endOffset"]
        start, end, startOffset, endOffset = self.check_fields(start, end, startOffset, endOffset, quote, self.document.id)
        d["ranges"][0]["start"] = start
        d["ranges"][0]["end"] = end
        d["ranges"][0]["startOffset"] = startOffset
        d["ranges"][0]["endOffset"] = endOffset
        self.data = json.dumps(d)
        self.tag = ', '.join(d["tags"])

    @staticmethod
    def as_list(qs=None, user=None):
        if qs is None:
            qs = Annotation.objects.all()
        return [
            obj.as_json(user=user)
            for obj in qs.order_by('-updated')
        ]

    def __unicode__(self):
        d = json.loads(self.data)["quote"]
        return self.document.doc_id.title + ' - ' + d

    class Meta:
        verbose_name = _('annotation')
        verbose_name_plural = _('annotations')


class Token(models.Model):
    token = models.CharField(max_length=200, db_index=True)
    doc = models.ForeignKey(Document)
    sent = models.ForeignKey(Sentence)
    num = models.IntegerField()
    punctl = models.CharField(max_length=900)
    punctr = models.CharField(max_length=900)
    sent_pos = models.CharField(max_length=50)

    def __unicode__(self):
        return self.token

    class Meta:
        verbose_name = _('token')
        verbose_name_plural = _('tokens')


class Morphology(models.Model):
    # stupid class name, will change it someday
    token = models.ForeignKey(Token)
    lem = models.CharField(max_length=100, db_index=True)
    lex = models.CharField(max_length=100, db_index=True)
    gram = models.CharField(max_length=100, db_index=True)

    def __unicode__(self):
        return self.lem + ' ' + self.lex + ' ' + self.gram

    class Meta:
        verbose_name = _('analysis')
        verbose_name_plural = _('analyses')