# coding=utf-8
__author__ = 'elmira'

import re
from collections import defaultdict
from annotator.models import Sentence
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from Corpus.db_utils import Database

from child_corpus.settings import PREFIX

jquery = "jQuery(function ($) {$('#***').annotator().annotator('addPlugin', 'Tags').annotator('addPlugin', 'Corr')" + \
         ".annotator('addPlugin', 'ReadOnlyAnnotations').annotator('addPlugin', 'Store', {prefix: '" \
         + PREFIX + "/document-annotations',annotationData: {'document': ***},loadFromSearch: {'document': ***}});});"

reg = re.compile(',| ')
regToken= re.compile('">(.*?)</span>', flags=re.U | re.DOTALL)
regSpans = re.compile('[.?,!:«(;#№–/...)»-]*<span .*?</span>[.?,!:«(;#№–/...)»-]*', flags=re.U | re.DOTALL)


class ShowSentence:
    def __init__(self, sent_id, num, expand):
        k = Sentence.objects.get(pk=sent_id)
        self.tagged = self.bold(k.tagged, num)
        self.id = sent_id
        self.doc_id = k.doc_id
        self.expand = ''

        for i in range(sent_id-expand, sent_id):
            try:
                sent = Sentence.objects.get(pk=i)
                self.expand += sent.tagged + ' '
            except:
                pass
        self.expand += self.tagged + ' '
        for i in range(sent_id+1, sent_id+expand+1):
            try:
                sent = Sentence.objects.get(pk=i)
                self.expand += sent.tagged + ' '
            except:
                pass


    def bold(self, tagged, num):
        s = regSpans.findall(tagged)
        for i in num:
            try:
                s[i-1] = regToken.sub('"><b>\\1</b></span>', s[i-1])
            except:
                pass  #todo find the bug here
        return ' '.join(s)


class SentBag:
    def __init__(self, e, l):
        self.dic = {key: Sent(e[key], []) for key in e}

    def update(self, e, fr, t):
        todel = []
        for key in self.dic:
            if key not in e:
                todel.append(key)
        for key in todel:
            del self.dic[key]
        for key in e:
            if key in self.dic:
                # if num >= 2:
                #     if not self.dic[key].poss_w:
                #         continue
                arr = self.get_word_nums(self.dic[key].bold_w, fr, t)
                n_b = set()
                for val in e[key]:
                    if val in arr:
                        self.dic[key].eds += 1
                        self.dic[key].poss_w.append(val)
                        self.dic[key].poss_w += list(arr[val])
                        n_b.update(arr[val])
                self.dic[key].bold_w = list(n_b)

    def get_word_nums(self, arr, fr, to):
        d = defaultdict(set)
        r = range(fr, to+1)
        for n in arr:
            for i in r:
                if i != 0:
                    d[n+i].add(n)
        return d

    def finalize(self, num):
        a = {}
        for i in self.dic:
            if self.dic[i].eds == num-1:
                a[i] = self.dic[i].poss_w
        return a


class Sent:
    def __init__(self, b, p):
        self.bold_w = b
        self.poss_w = p
        self.eds = 0


def get_subcorpus(query):
    req = 'SELECT id FROM `annotator_document` WHERE 1 '
    if u'checked' in query:
        req += 'AND checked=True '
    if u'annotated' in query:
        req += 'AND annotated=True '
    gender = query.get(u'gender').encode('utf-8')
    if gender != u'any':
        req += 'AND gender="'+ gender +'" '
    date1 = query.get(u'date1')
    if date1 != u'':
        req += 'AND date>='+ date1 +' '
    date2 = query.get(u'date2')
    if date2 != u'':
        req += 'AND date<='+ date2 +' '
    db = Database()
    docs = [str(i[0]) for i in db.execute(req)]
    subsum = db.execute('SELECT SUM(sentences), SUM(words) FROM `annotator_document` WHERE id IN (' +req + ')')
    flag = False if req == 'SELECT id FROM `annotator_document` WHERE 1 ' else True
    return docs, subsum[0][0], subsum[0][1], flag


def make_small_query(arr, title):
    one = []
    s = ''
    for l in arr:
        one.append(title + '="'+ l.encode('utf-8') +'"')
    if len(one) == 1:
        s += 'AND '+ one[0] + ';'
    else:
        s += 'AND (' + ' OR '.join(one) + ')'
    return s


def bold(word, sent):
    s = re.sub('('+word+')', '<b>\\1</b>', sent)
    return s


def pages(sent_list, page, num):
    paginator = Paginator(sent_list, num)
    try:
        sents = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        sents = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        sents = paginator.page(paginator.num_pages)
    return sents


def exact_search(word, docs, flag, expand, page, per_page):
    db = Database()
    word = word.split()[0]
    req1 = 'SELECT COUNT(DISTINCT doc_id) FROM `annotator_token` WHERE token="'+word + '" '
    if flag:
        req1 += 'AND doc_id IN ('+','.join(docs) + ');'
    docs_len = int(db.execute(req1)[0][0])
    n_req = 'SELECT COUNT(DISTINCT sent_id) FROM `annotator_token` WHERE token="'+ word +'" '
    if flag:
        n_req += 'AND doc_id IN ('+','.join(docs) + ');'
    sent_num = int(db.execute(n_req)[0][0])
    req2 = 'SELECT DISTINCT sent_id FROM `annotator_token` WHERE token="'+ word +'" '
    if flag:
        req2 += 'AND doc_id IN ('+','.join(docs) + ')'
    req2 += ' LIMIT %d,%d;' %((page - 1)*per_page, per_page)
    sentences = '(' + ', '.join([str(i[0]) for i in db.execute(req2)]) + ')'
    if sentences != '()':
        req3 = 'SELECT sent_id, num FROM `annotator_token` WHERE token="'+ word +'" AND sent_id IN ' + sentences
        tokens = db.execute(req3)
    else:
        tokens = []
    e = defaultdict(list)
    for i, j in tokens:
        e[i].append(j)
    jq = []
    sent_list = [ShowSentence(i, e[i], expand) for i in e]
    for sent in sent_list:
        jq.append(jquery.replace('***', str(sent.id)))
    return jq, sent_list, word, docs_len, sent_num

def lex_search(query, docs, flag, expand, page, per_page):
    words = query.getlist(u'wordform[]')
    lexis = query.getlist(u'lex[]')
    grams = query.getlist(u'grammar[]')
    errs = query.getlist(u'errors[]')


    froms = [int(i) for i in query.getlist(u'from[]') if i != '']
    tos = [int(i) for i in query.getlist(u'to[]') if i != '']
    if any(i != '' for i in [words[1], lexis[1], grams[1], errs[1]]):
        return lex_full_search(words, lexis, grams, errs, froms, tos, docs, flag, expand, page, per_page)
    jq = []
    wn = 0
    word = words[wn].lower().encode('utf-8')
    lex = lexis[wn].encode('utf-8')
    gram = grams[wn].encode('utf-8')
    err = errs[wn].encode('utf-8')
    rows, sent_num, d_num = collect_data([word, lex, gram, err, docs, flag, page, per_page])
    e = defaultdict(list)
    if rows:
        if len(rows[0]) == 2:
            for i, j in rows:
                e[i].append(j)
        else:
            for i, j, k in rows:
                for n in range(j, k+1):
                    e[i].append(n)
    sent_list = [ShowSentence(i, e[i], expand) for i in e]
    for sent in sent_list:
        jq.append(jquery.replace('***', str(sent.id)))
    return jq, sent_list, ' '.join([word, lex, gram, err]), d_num, sent_num


def lex_full_search(words, lexis, grams, errs, froms, tos, docs, flag, expand, page, per_page):
    jq = []
    a = {}
    s = ''
    for wn in range(len(words)):
        word = words[wn].lower().encode('utf-8')
        lex = lexis[wn].encode('utf-8')
        gram = grams[wn].encode('utf-8')
        err = errs[wn].encode('utf-8')
        rows, sent_num, d_num = collect_full_data([word, lex, gram, err, docs, flag, page, per_page])
        e = defaultdict(list)
        if rows:
            if len(rows[0]) == 2:
                for i, j in rows:
                    e[i].append(j)
            else:
                for i, j, k in rows:
                    for n in range(j, k+1):
                        e[i].append(n)
        if not a:
            a = SentBag(e, len(words))
            s += ' '.join([word, lex, gram, err])
        else:
            fr, t = froms[wn-1], tos[wn-1]
            s += '<br><small>на расстоянии %d, %d от </small><br> ' %(fr, t)+ ' '.join([word, lex, gram, err])
            a.update(e, fr, t)
    a = a.finalize(len(words))
    sent_list = [ShowSentence(i, a[i], expand) for i in a]
    sent_num = len(sent_list)
    d_num = len(set(i.doc_id for i in sent_list))
    sent_list = sorted(sent_list, key=lambda i: i.id)[per_page*(page-1):per_page*page]
    for sent in sent_list:
        jq.append(jquery.replace('***', str(sent.id)))
    return jq, sent_list, s, d_num, sent_num


def collect_data(arr):
    db = Database()
    word, lex, gram, err, docs, flag, page, per_page = arr
    err = err.strip()
    s = bincode(word, lex, gram, err)
    if s == '0000':
        return [], 0, 0
    elif s == '0001':
        req_template = ''' FROM annotator_annotation
                 LEFT JOIN annotator_sentence
                 ON annotator_annotation.document_id = annotator_sentence.id WHERE 1 '''
        req_template += parse_gram(err, 'tag')
        if flag:
            req_template += 'AND doc_id_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT document_id)''' + req_template
        req1 = 'SELECT DISTINCT document_id' + req_template
        req = 'SELECT DISTINCT document_id, start, end' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id_id)''' + req_template
    elif s == '0010':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 '''+ parse_gram(gram, 'gram')
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0011':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 %s AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s''' %(parse_gram(err, 'tag'), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0100':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 '''
        req_template += parse_lex(lex)
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0101':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 %s AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s''' %(parse_gram(err, 'tag'), parse_lex(lex))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0110':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 %s %s''' %(parse_lex(lex), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0111':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 %s AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s %s''' %(parse_gram(err, 'tag'), parse_lex(lex), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1000':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 AND lem="%s" ''' %word
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1001':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 AND lem="%s" AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s ''' %(word,parse_gram(err, 'tag'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1010':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 AND lem="%s" %s''' %(word, parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1011':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 AND lem="%s" AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s %s''' %(word,parse_gram(err, 'tag'), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1100':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 AND lem="%s" %s''' %(word, parse_lex(lex))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1101':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 AND lem="%s" AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s %s''' %(word,parse_gram(err, 'tag'), parse_lex(lex))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1110':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 AND lem="%s" %s %s ''' %(word, parse_lex(lex), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    else:
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 AND lem="%s" AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s %s %s''' %(word,parse_gram(err, 'tag'), parse_lex(lex), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    req1 += ' LIMIT %d,%d;' %((page - 1)*per_page, per_page)
    sentences = '(' + ', '.join([str(i[0]) for i in db.execute(req1)]) + ')'
    if sentences == '()':
        return [], 0, 0
    if s == '0001':
        req += ' AND document_id IN ' + sentences
    else:
        req += ' AND sent_id IN ' + sentences

    rows = db.execute(req)
    sent_num = int(db.execute(n_req)[0][0])
    d_num = int(db.execute(d_req)[0][0])
    return rows, sent_num, d_num


def parse_lex(lex):
    req = ''
    arr = ['lex LIKE "' + gr.strip() + '"' for gr in lex.replace(')', '').replace('(', '').split('|')]
    if len(arr) == 1:
        req += 'AND '+ arr[0] + ' '
    else:
        req += 'AND (' + ' OR '.join(arr) + ') '
    return req


def parse_gram(gram, t):
    req = ''
    arr = gram.split(',')
    for gr in arr:
        one = [t + ' LIKE "%' + i.strip() + '%"' for i in gr.replace(')', '').replace('(', '').split('|')]
        if len(one) == 1:
            req += 'AND '+ one[0] + ' '
        else:
            req += 'AND (' + ' OR '.join(one) + ') '
    return req


def bincode(a,b,c,d):
    s = ''
    for i in [a,b,c,d]:
        s += '1' if i else '0'
    return s

def collect_full_data(arr):
    db = Database()
    word, lex, gram, err, docs, flag, page, per_page = arr
    err = err.strip()
    s = bincode(word, lex, gram, err)
    if s == '0000':
        return [], 0, 0
    elif s == '0001':
        req_template = ''' FROM annotator_annotation
                 LEFT JOIN annotator_sentence
                 ON annotator_annotation.document_id = annotator_sentence.id WHERE 1 '''
        req_template += parse_gram(err, 'tag')
        if flag:
            req_template += 'AND doc_id_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT document_id)''' + req_template
        req1 = 'SELECT DISTINCT document_id' + req_template
        req = 'SELECT DISTINCT document_id, start, end' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id_id)''' + req_template
    elif s == '0010':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 '''+ parse_gram(gram, 'gram')
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0011':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 %s AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s''' %(parse_gram(err, 'tag'), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0100':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 '''
        req_template += parse_lex(lex)
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0101':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 %s AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s''' %(parse_gram(err, 'tag'), parse_lex(lex))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0110':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 %s %s''' %(parse_lex(lex), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '0111':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 %s AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s %s''' %(parse_gram(err, 'tag'), parse_lex(lex), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1000':
        req = '''SELECT DISTINCT sent_id, num FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 AND lem="%s" ''' %word
        if flag:
            req += 'AND doc_id IN ('+','.join(docs)+')'
    elif s == '1001':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 AND lem="%s" AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s ''' %(word,parse_gram(err, 'tag'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1010':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 AND lem="%s" %s''' %(word, parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1011':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 AND lem="%s" AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s %s''' %(word,parse_gram(err, 'tag'), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1100':
        req_template = ''' FROM  annotator_morphology
        LEFT JOIN annotator_token
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 AND lem="%s" %s''' %(word, parse_lex(lex))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1101':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 AND lem="%s" AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s %s''' %(word,parse_gram(err, 'tag'), parse_lex(lex))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    elif s == '1110':
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        WHERE 1 AND lem="%s" %s %s ''' %(word, parse_lex(lex), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    else:
        req_template = ''' FROM  annotator_token
        LEFT JOIN annotator_morphology
        ON annotator_token.id = annotator_morphology.token_id
        LEFT JOIN annotator_annotation
        ON annotator_token.sent_id = annotator_annotation.document_id
        WHERE 1 AND lem="%s" AND num>= annotator_annotation.start AND num <= annotator_annotation.end %s %s %s''' %(word,parse_gram(err, 'tag'), parse_lex(lex), parse_gram(gram, 'gram'))
        if flag:
            req_template += 'AND doc_id IN ('+','.join(docs)+')'
        n_req = '''SELECT COUNT(DISTINCT sent_id)''' + req_template
        req = 'SELECT DISTINCT sent_id, num' + req_template
        req1 = 'SELECT DISTINCT sent_id' + req_template
        d_req = '''SELECT COUNT(DISTINCT doc_id)''' + req_template
    rows = db.execute(req)
    return rows, 0,0