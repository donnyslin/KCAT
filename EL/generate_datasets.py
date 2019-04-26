import pickle as pkl
import json
import nltk
from nltk.tokenize import WordPunctTokenizer
import sys
def generate_doc():
    content = sys.argv[1]
    offset = sys.argv[2].split(':')
    D={
    "test":{
    "Content":"",
    "Mentions":
    [
    ]
    }
    }
    D['test']['Content'] = content
    for o in offset:
        b,e = o.split('-')
        b=int(b)
        e=int(e)
        D['test']['Mentions'].append({"start": b, "end": e, "surface_form": content[b:e+1], "entity": ''})
    return D


root_path = '../pkl/'
Documents = generate_doc()#json.load(open(root_path+'doc.json','rb'))
mid2pid = pkl.load(open(root_path+'mid2pid.pkl','rb'))
pid2name = pkl.load(open(root_path+'pid2name.pkl','rb'))
pid2mid={}
name2pid={}
for mid,pid in mid2pid.items():
    pid2mid[pid]=mid
for pid,name in pid2name.items():
    name2pid[name]=pid

pme = pkl.load(open(root_path+'pme_lower.pkl','rb'))



def splitSentence(paragraph):
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    sentences = tokenizer.tokenize(paragraph)
    return sentences

def wordtokenizer(sentence):
    #分段
    words = WordPunctTokenizer().tokenize(sentence)
    return words

def gene_dataset(Documents):
    conll_file = open('/home/linsheng/TAC2018/mulrel-nel/data/basic_data/test_datasets/wned-datasets/tac/tac.conll', 'w')
    csv_file = open('/home/linsheng/TAC2018/mulrel-nel/data/generated/test_train_data/tac.csv', 'w')
    doc_contents = {}
    punctuations = [',', '.', '!', '?']
    wiki_prefix = 'en.wikipedia.org/wiki/'
    Dataset = {}
    for doc in Documents:
        mentions = Documents[doc]['Mentions']
        content = Documents[doc]['Content']
        content_ = content
        for i in range(len(mentions) - 1, -1, -1):
            begin, end, mention, entity = mentions[i]['start'], mentions[i]['end'], mentions[i]['surface_form'], \
                                          mentions[i]['entity']
            content_ = content_[:begin] + ' TACENTITY%05d ' % i + content_[end + 1:]

        tokens = []
        entity_pos = []
        # conll
        for sentence in splitSentence(content_):
            for word in wordtokenizer(sentence):
                if word.startswith('TACENTITY'):
                    entity_pos.append(len(tokens))
                tokens.append(word)
            tokens.append('')
        #print(tokens,doc)
        conll_file.write('-DOCSTART- (' + doc + '\n')
        for i, token in enumerate(tokens):
            if token.startswith('TACENTITY'):
                idx = int(token[9:])
                m = mentions[idx]
                words = nltk.word_tokenize(m['surface_form'] + '!')[0:-1]
                for i, word in enumerate(words):
                    if i == 0:
                        ss = [word, 'B', m['surface_form'], m['entity'].replace('_', ' '), wiki_prefix + m['entity'],
                              '000', '000\n']
                    else:
                        ss = [word, 'I', m['surface_form'], m['entity'].replace('_', ' '), wiki_prefix + m['entity'],
                              '000', '000\n']
                    conll_file.write('\t'.join(ss))
            else:
                conll_file.write(token + '\n')
                pass
        # csv
        if not len(mentions) == len(entity_pos):
            print(doc, len(mentions), len(entity_pos))
        Dataset[doc] = {'Content': content, 'Mentions': []}
        for i, m in enumerate(mentions):
            m = mentions[i]
            begin, end, mention, entity = mentions[i]['start'], mentions[i]['end'], mentions[i]['surface_form'], \
                                          mentions[i]['entity']
            entity = entity.replace('_', ' ')
            # context
            idx = entity_pos[i]
            l_context = []
            r_context = []
            for j in range(i - 1, -1, -1):
                token = tokens[j]
                if token.startswith('TACENTITY'):
                    idx = int(token[9:])
                    mm = mentions[idx]
                    words = nltk.word_tokenize(mm['surface_form'] + '!')[0:-1]
                    for word in words[::-1]:
                        l_context.append(word)
                else:
                    l_context.append(token)
                if len(l_context) > 50:
                    break
            for j in range(i + 1, len(tokens)):
                token = tokens[j]
                if token.startswith('TACENTITY'):
                    idx = int(token[9:])
                    mm = mentions[idx]
                    words = nltk.word_tokenize(mm['surface_form'] + '!')[0:-1]
                    for word in words:
                        if word in punctuations:
                            continue
                        r_context.append(word)
                else:
                    if token in punctuations:
                        continue
                    r_context.append(token)
                if len(r_context) > 50:
                    break
            l_context = l_context[:50][::-1]
            m['l_context'] = l_context
            m['r_context'] = r_context
            # candidates
            if not mention.lower() in pme:
                candidates = []
            else:
                counts = pme[mention.lower()]
                tot = 0
                for pid in counts:
                    count = counts[pid]
                    tot += count
                candidates = []
                for pid in counts:
                    if not int(pid) in pid2name:
                        continue
                    candidates.append([str(pid), str(float(counts[pid]) / tot), pid2name[int(pid)]])
                del candidates[50:]
                candidates = sorted(candidates, key=lambda x: float(x[1]), reverse=True)
            m['Candidates'] = []
            for candidate in candidates:
                m['Candidates'].append(dict(zip(['pid', 'prior', 'name'], candidate)))
            # del m['Candidates'][50:]
            csv_file.write(doc + '\t' + doc + '\t' + mention + '\t' + ' '.join(l_context) + '\t' + ' '.join(r_context))
            if len(candidates) == 0:
                csv_file.write('\t' + 'EMPTYCAND')
                m['true_pos'] = -1
                csv_file.write('\tGT:\t' + '-1' + ',' + str(name2pid[entity]) +
                               ',' + pid2name[name2pid[entity]] + '\n')
            else:
                csv_file.write('\t' + 'CANDIDATES')
                idx = 0
                if entity == 'NIL':
                    idx = 1
                else:
                    for i, candidate in enumerate(candidates):
                        if str(name2pid[entity]) == candidate[0]:
                            idx = i + 1
                        csv_file.write('\t' + ','.join(candidate))
                if idx > 0:
                    m['true_pos'] = idx - 1
                    csv_file.write('\tGT:\t' + str(idx) + ',' + ','.join(candidates[idx - 1]) + '\n')
                else:
                    m['true_pos'] = -1
                    csv_file.write('\tGT:\t' + '-1' + ',' + str(name2pid[entity]) +
                                   ',' + entity + '\n')
            Dataset[doc]['Mentions'].append(m)
    return Dataset


def load_person_names(path):
    data = []
    with open(path, 'r', encoding='utf8') as f:
        for line in f:
            data.append(line.strip().replace(' ', '_'))
    return set(data)

def find_coref(ment, mentlist, person_names):
    cur_m = ment['surface_form'].lower()
    coref = []
    for m in mentlist:
        #if len(m['Candidates']) > 0:
        #    print(m['Candidates'][0])
        if len(m['Candidates']) == 0 or m['Candidates'][0]['name'].replace(' ','_') not in person_names:
            continue

        mention = m['surface_form'].lower()
        start_pos = mention.find(cur_m)
        if start_pos == -1 or mention == cur_m:
            continue

        end_pos = start_pos + len(cur_m) - 1
        if (start_pos == 0 or mention[start_pos-1] == ' ') and \
                (end_pos == len(mention) - 1 or mention[end_pos + 1] == ' '):
            coref.append(m)

    return coref

def with_coref(dataset, person_names):
    for doc in dataset:
        mentions = dataset[doc]['Mentions']
        for cur_m in mentions:
            coref = find_coref(cur_m, mentions, person_names)
            if coref is not None and len(coref) > 0:
                cur_cands = {}
                cur_names = {}
                for m in coref:
                    for cand in m['Candidates']:
                        c, p ,name = cand['pid'], float(cand['prior']), cand['name']
                        cur_cands[c] = cur_cands.get(c, 0) + p
                        cur_names[c] = name
                cc = []
                for c in cur_cands.keys():
                    cur_cands[c] /= len(coref)
                    cc.append(dict({'pid':c, 'prior':cur_cands[c], 'name':cur_names[c]}))
                cur_m['Candidates'] = sorted(cc, key=lambda x: x['prior'])[::-1]
                cur_m['true_pos']=-1
                #print(cur_m['entity'])
                for i,c in  enumerate(cur_m['Candidates']):
                    if cur_m['entity'].replace('_',' ') == c['name']:
                        cur_m['true_pos'] = i


Dataset = gene_dataset(Documents)
#person_names = load_person_names(root_path+'persons.txt')
#with_coref(Dataset, person_names)
#pkl.dump(Dataset, open(root_path+'ms_dataset_coref_v5.pkl','wb'))
