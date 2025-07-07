import os
import csv
from urllib.parse import quote
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import DC, DCTERMS, RDF, XSD

# prefixes
BASE   = "http://example.org/resource/"
SCHEMA = Namespace("http://schema.org/")
EDM    = Namespace("http://www.europeana.eu/schemas/edm/")
MO     = Namespace("http://purl.org/ontology/mo/")
CRM    = Namespace("http://www.cidoc-crm.org/cidoc-crm/")  
NS2    = RDF                                              

 # initializing an RDF graph and bind prefixes
g = Graph()
g.bind("dc",      DC)
g.bind("dcterms", DCTERMS)
g.bind("edm",     EDM)
g.bind("mo",      MO)
g.bind("ns1",     CRM)
g.bind("ns2",     NS2)
g.bind("schema",  SCHEMA)
g.bind("xsd",     XSD)

def add_triple(row):
    # deleting whitespace from all the values in a CSV row
    row = {k.strip(): v.strip() for k, v in row.items()}

    # subject. if the subject is already a URI, use it 
    subj_val = row['subject']
    if subj_val.startswith("http"):
        subj = URIRef(subj_val)
    else:
        safe_subj = quote(subj_val, safe='')   # if not add the base URI
        subj = URIRef(BASE + safe_subj)

    # predicate. splitting prefix and local name
    pred_val = row['predicate']
    if ":" in pred_val:
        prefix, local = [p.strip() for p in pred_val.split(":", 1)]
        mapping = {
            'dc':      DC,
            'dcterms': DCTERMS,
            'edm':     EDM,
            'mo':      MO,
            'schema':  SCHEMA,
            'ns1':     CRM,
            'ns2':     NS2,
        }
        ns = mapping.get(prefix)
        if ns:
            pred = ns[local] # use corresponding namespace
        else:
            # if unknown prefix, percent-encode and use base URI
            pred = URIRef(BASE + quote(pred_val, safe=''))
    else: #if no prefix,  percent-encode and use base URI
        pred = URIRef(BASE + quote(pred_val, safe=''))

    # object
    obj_val = row['object']
    if obj_val.startswith("http"):
        obj = URIRef(obj_val) # if object=URI, use it 
    else:
        parts = obj_val.split("-")
        if len(parts) == 3 and all(p.isdigit() for p in parts): # if it looks like a date, create a typed literal for date values
            obj = Literal(obj_val, datatype=XSD.date)
        else: # if not, create a plain string literal
            obj = Literal(obj_val, datatype=XSD.string)

    g.add((subj, pred, obj))


# processing all the csv files
DATA_DIR = "/Users/arinasamylova/Downloads/csv"  # open CSV folder

for fname in os.listdir(DATA_DIR):
    if not fname.lower().endswith(".csv"): # skip non-CSV files
        continue
    path = os.path.join(DATA_DIR, fname)
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # check if required columns exist
        if set(reader.fieldnames) >= {'subject', 'predicate', 'object'}:
            for row in reader:
                add_triple(row)
        else: #raise an error if the CSV doesn't have necessary headers
            raise ValueError(f"In file {fname} expected subject,predicate,object")

# serialize graph to turtle
g.serialize(destination="dataset.ttl", format="turtle")
print("dataset.ttl")