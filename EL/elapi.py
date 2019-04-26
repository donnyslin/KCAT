import sys
sys.path.append('../')
from nel import *
import nel.testdataset as D
from nel.mulrel_ranker import MulRelRanker
from nel.ed_ranker import EDRanker
import nel.utils as utils
from pprint import pprint
import argparse
import pickle as pkl
import json
import nltk
from nltk.tokenize import WordPunctTokenizer
import sys
import copy
from flask import Flask, jsonify, abort, request
import requests
app = Flask(__name__)
parser = argparse.ArgumentParser()

datadir = '../data/generated/test_train_data'
conll_path = '../data/basic_data/test_datasets'
person_path = '../data/basic_data/p_e_m_data/persons.txt'
voca_emb_dir = '../data/generated/embeddings/word_ent_embs/'
print(torch.cuda.is_available())
ModelClass = MulRelRanker


# general args
parser.add_argument("--mode", type=str,
                    help="train or eval",
                    default='eval')
parser.add_argument("--model_path", type=str,
                    help="model path to save/load",
                    default='../model')

# args for preranking (i.e. 2-step candidate selection)
parser.add_argument("--n_cands_before_rank", type=int,
                    help="number of candidates",
                    default=30)
parser.add_argument("--prerank_ctx_window", type=int,
                    help="size of context window for the preranking model",
                    default=50)
parser.add_argument("--keep_p_e_m", type=int,
                    help="number of top candidates to keep w.r.t p(e|m)",
                    default=4)
parser.add_argument("--keep_ctx_ent", type=int,
                    help="number of top candidates to keep w.r.t using context",
                    default=4)

# args for local model
parser.add_argument("--ctx_window", type=int,
                    help="size of context window for the local model",
                    default=100)
parser.add_argument("--tok_top_n", type=int,
                    help="number of top contextual words for the local model",
                    default=25)


# args for global model
parser.add_argument("--mulrel_type", type=str,
                    help="type for multi relation (rel-norm or ment-norm)",
                    default='ment-norm')
parser.add_argument("--n_rels", type=int,
                    help="number of relations",
                    default=5)
parser.add_argument("--hid_dims", type=int,
                    help="number of hidden neurons",
                    default=100)
parser.add_argument("--snd_local_ctx_window", type=int,
                    help="local ctx window size for relation scores",
                    default=6)
parser.add_argument("--dropout_rate", type=float,
                    help="dropout rate for relation scores",
                    default=0.3)


# args for training
parser.add_argument("--n_epochs", type=int,
                    help="max number of epochs",
                    default=200)
parser.add_argument("--dev_f1_change_lr", type=float,
                    help="dev f1 to change learning rate",
                    default=0.915)
parser.add_argument("--n_not_inc", type=int,
                    help="number of evals after dev f1 not increase",
                    default=10)
parser.add_argument("--eval_after_n_epochs", type=int,
                    help="number of epochs to eval",
                    default=5)
parser.add_argument("--learning_rate", type=float,
                    help="learning rate",
                    default=1e-4)
parser.add_argument("--margin", type=float,
                    help="margin",
                    default=0.01)

# args for LBP
parser.add_argument("--df", type=float,
                    help="dumpling factor (for LBP)",
                    default=0.5)
parser.add_argument("--n_loops", type=int,
                    help="number of LBP loops",
                    default=10)
args = parser.parse_args()

def generate_doc(content, offset):
    for word in content.split(' '):
        print(word, content.find(word), content.find(word)+len(word)-1)
    D = {
            "test":{
                "Content":"",
                "Mentions":[]
            }
        }
    D['test']['Content'] = content
    for o in offset:
        b,e = o.split('-')
        b=int(b)
        e=int(e)
        D['test']['Mentions'].append({"start": b, "end": e, "surface_form": content[b:e+1], "entity": ''})
    return D

def splitSentence(paragraph):
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    sentences = tokenizer.tokenize(paragraph)
    return sentences

def wordtokenizer(sentence):
    words = WordPunctTokenizer().tokenize(sentence)
    return words

def gene_dataset(Documents):
    conll_file = open('../data/basic_data/test_datasets/wned-datasets/tac/tac.conll', 'w')
    csv_file = open('../data/generated/test_train_data/tac.csv', 'w')
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

@app.route('/edl/ranking/', methods=['POST','GET'])
def ranking():
    content = request.args.get('text')
    offset = request.args.get('offset').split(':')
    try:
        cands = int(request.args.get('cands'))
    except:
        cands = 1
    Documents = generate_doc(content, offset)
    gene_dataset(copy.deepcopy(Documents))
    conll.load_dataset(datadir, conll_path)
    dev_datasets = [('tac', conll.tac)]
    data = ranker.get_data_items(conll.tac, predict=True)
    vecs = ranker.model.rel_embs.cpu().data.numpy()
    ranker.model._coh_ctx_vecs = []
    predictions = ranker.predict(data, cands)
    entities = []
    for _, preds in predictions.items():
        for pred in preds:
            entities.append(pred['pred'][0])
    for _, doc in Documents.items():
        for i, mention in enumerate(doc['Mentions']):
            mention['entity'] = entities[i]
    print(doc['Mentions'])
    return json.dumps(doc['Mentions'])

if __name__ == "__main__":
    root_path = '../pkl/'
    mid2pid = pkl.load(open(root_path + 'mid2pid.pkl', 'rb'))
    pid2name = pkl.load(open(root_path + 'pid2name.pkl', 'rb'))
    pid2mid = {}
    name2pid = {}
    for mid, pid in mid2pid.items():
        pid2mid[pid] = mid
    for pid, name in pid2name.items():
        name2pid[name] = pid
    pme = pkl.load(open(root_path + 'pme_lower.pkl', 'rb'))

    print('load conll at', datadir)
    conll = D.CoNLLDataset(person_path)
    print('create model')
    word_voca, word_embeddings = utils.load_voca_embs(voca_emb_dir + 'dict.word',
                                                      voca_emb_dir + 'word_embeddings.npy')
    print('word voca size', word_voca.size())
    snd_word_voca, snd_word_embeddings = utils.load_voca_embs(voca_emb_dir + '/glove/dict.word',
                                                              voca_emb_dir + '/glove/word_embeddings.npy')
    print('snd word voca size', snd_word_voca.size())
    entity_voca, entity_embeddings = utils.load_voca_embs(voca_emb_dir + 'dict.entity',
                                                          voca_emb_dir + 'entity_embeddings.npy')
    config = {'hid_dims': args.hid_dims,
              'emb_dims': entity_embeddings.shape[1],
              'freeze_embs': True,
              'tok_top_n': args.tok_top_n,
              'margin': args.margin,
              'word_voca': word_voca,
              'entity_voca': entity_voca,
              'word_embeddings': word_embeddings,
              'entity_embeddings': entity_embeddings,
              'snd_word_voca': snd_word_voca,
              'snd_word_embeddings': snd_word_embeddings,
              'dr': args.dropout_rate,
              'args': args}

    if ModelClass == MulRelRanker:
        config['df'] = args.df
        config['n_loops'] = args.n_loops
        config['n_rels'] = args.n_rels
        config['mulrel_type'] = args.mulrel_type
    else:
        raise Exception('unknown model class')

    ranker = EDRanker(config=config)
    app.run(host='0.0.0.0', port=5555)
