import pickle as pkl
import json
import pandas as pd
import csv

#mn = dict()
# with open('./resources/mid2name.tsv','r', encoding='utf-8') as f:
#     for line in f:
#         if not len(line.strip().split('\t')) == 2:
#             continue
#         mid = line.strip().split('\t')[0]
#         name = line.strip().split('\t')[1]
#         if not mid.replace('/','.')[1:] in mn:
#             mn[mid.replace('/', '.')[1:]] = []
#         mn[mid.replace('/','.')[1:]].append(name)
#
# entity_types_mapping= dict()
# with open('./resources/BBN/type_entities.txt', 'r') as f:
#     for line in f:
#         line = line.strip()
#         type = line.split('\t')[0]
#         for ent in line.split('\t')[1].split(';'):
#             ent = ent[:-1].split('/')[-1]
#             if ent in mn:
#                 ents = mn[ent]
#             else:
#                 continue
#             for ent in ents:
#                 ent = ent.replace(' ','_')
#                 if not ent in entity_types_mapping:
#                     entity_types_mapping[ent] = []
#                 entity_types_mapping[ent].append(type)
#
# for ent in entity_types_mapping:
#     types = entity_types_mapping[ent]
#     leaf_types = []
#     for t1 in types:
#         flag = 1
#         for t2 in types:
#             if not t1==t2 and t2.startswith(t1):
#                 flag = False
#                 break
#         if flag:
#             leaf_types.append(t1)
#     entity_types_mapping[ent] = leaf_types
#
# json.dump(entity_types_mapping, open('./resources/BBN/entity2path.json','w'))

#type2son.json.json
types = pkl.load(open('./resources/BBN/type.pkl','rb'))
print(types[1])
# type2son.json = dict()
# for t in types[0]:
#     type2son.json[t.split('/')[-1]] = []
# for fa in types[1]:
#     for son in types[1][fa]:
#         type2son.json[fa.split('/')[-1]].append(son.split('/')[-1])
# json.dump(type2son.json, open('./resources/BBN/type2son.json.json','w'))
