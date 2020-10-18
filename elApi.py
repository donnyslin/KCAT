import requests
import json
import numpy as np
def api(text, spans, url="http://10.214.155.249:5555"):
    offset = []
    for span in spans:
        offset.append(str(span[0])+'-'+str(span[1]))
    offset = ':'.join(offset)
    res = requests.post(
        url='%s/edl/ranking/?text=%s&&offset=%s&&cands=2' % (url, text, offset))
    return json.loads(res.text)

def EL(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = ""
        spans = []
        flag = 0
        for line in f:
            if line.strip() == '%%TYPE_ANNOTATIONS%%':
                flag = 1
                continue
            if flag == 0:
                text += line
            else:
                spans.append([line.split('\t')[0], line.split('\t')[1]])
    return api(text, spans)

# import sys
# import os
# rootPath = './doc'
# entities = set()
# for file in os.listdir('./doc'):
#     try:
#         rlt = EL(rootPath + os.sep + file)
#     except Exception as e:
#         continue
#     for em in rlt:
#         for ent in em['entity']:
#             if not entities == 'NIL':
#                 entities.add(ent)
#
# import json
# fp = json.load(open('./resources/fp.json', 'r'))
# fp_simple = dict()
# for ent in fp:
#     if ent in entities:
#         fp_simple[ent] = fp[ent]
# json.dump(fp_simple, open('./resources/fp_simple.json', 'w'))
#
# rootPaths = ['./resources/BBN', './resources/Wiki', './resources/DBpedia']
# for path in rootPaths:
#     e2p = json.load(open(path+os.sep+'entity2path.json', 'r'))
#     e2p_simple = dict()
#     for ent in e2p:
#         if ent in entities:
#             e2p_simple[ent] = e2p[ent]
#     json.dump(e2p_simple, open(path+os.sep+'entity2path_simple.json', 'w'))
