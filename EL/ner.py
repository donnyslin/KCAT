import spacy
nlp = spacy.load('en')
s = 'Heat beats Lakers' 
doc = nlp(s)
words = []
pos = 0
for x in doc:
    ent = str(x)
    iob = str(x.ent_iob_)
    t = x.ent_type_
    if iob == 'B':
        words = [ent]
    elif iob == 'I':
        words.append(ent)
    else:
       if len(words)>0:
           idx = []
           for word in words:
               idx.append(s.find(word,pos))
               pos = idx[-1]+len(word)
           print(idx[0], pos-1, s[idx[0]:pos])
       words = []
    

