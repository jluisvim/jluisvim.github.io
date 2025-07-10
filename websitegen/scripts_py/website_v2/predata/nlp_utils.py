# nlp_utils.py
import stanza
import os

# Initialize Stanza NLP pipeline
print("Loading NLP model...")
if not os.path.isdir('/home/jluis/stanza_resources'):
    print('Downloading Stanza resources...')
    stanza.download("en")
nlp = stanza.Pipeline(lang="en", processors="tokenize,ner,pos,lemma,depparse", use_gpu=False)

def analyze_text(text):
    doc = nlp(text)
    return {
        "entities": extract_entities(doc),
        "relationships": extract_relationships(doc),
        "events": extract_events(doc)
    }

def extract_entities(doc):
    return [(ent.text, ent.type) for sent in doc.sentences for ent in sent.ents]

def extract_relationships(doc):
    relationships = []
    for sent in doc.sentences:
        verbs = [word for word in sent.words if word.upos == "VERB"]
        for verb in verbs:
            subj = [word.text for word in sent.words if word.head == verb.id and word.deprel in ("nsubj", "nsubj:pass")]
            obj = [word.text for word in sent.words if word.head == verb.id and word.deprel in ("obj", "dobj")]
            if subj and obj:
                relationships.append({
                    "subject": " ".join(subj),
                    "verb": verb.text,
                    "object": " ".join(obj),
                    "lemma": verb.lemma
                })
    return relationships

def extract_events(doc):
    events = []
    for sent in doc.sentences:
        for word in sent.words:
            if word.upos == "VERB":
                context_words = [w.text for w in sent.words[max(0, word.id - 2):word.id + 3]]
                events.append({
                    "text": word.text,
                    "lemma": word.lemma,
                    "context": " ".join(context_words)
                })
    return events
