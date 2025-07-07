# module that helps to parse our xml/tei file: 
# to read tags, attributes, text...
import xml.etree.ElementTree as ET

# library RDFLib helps to work with rdf:
# Graph     — storage for all triples
# Namespace — easy way to handle prefix + URI
# URIRef    — to create resources by URI
# Literal   — to create values (strings, numbers, dates)
from rdflib import Graph, Namespace, URIRef, Literal

# importing basic namespaces and predicates
# RDF      — rdf:type and basic RDF concepts
# XSD      — xsd:date, xsd:integer, and other literal types
# OWL      — owl:sameAs and other ontology terms
# DC       — dc:title, dc:creator, etc. (Dublin Core Elements)
# DCTERMS  — dcterms:date, dcterms:subject, etc. (Dublin Core Terms)
from rdflib.namespace import RDF, XSD, OWL, DC, DCTERMS, SKOS, FOAF

# module in order to use it in a URI as a unique identifiers
import hashlib

from rdflib import BNode
from rdflib.collection import Collection

# parse the XML file
#reading our xml file and keeping info into tree variable
tree = ET.parse('/Users/arinasamylova/Downloads/declaration.xml')
# defining the root that contains tags
root = tree.getroot()

# revealing uri namespace of the root tag
# print(root.tag) # {http://www.tei-c.org/ns/1.0}TEI

# creating namespace in a form of dictionary (it will help find/findall to work)
ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

# creating empty graph for triples
g = Graph()

# namespace for our specific needs (local entities related to the UDHR)
EX  = Namespace('https://polinakhrm.github.io/udhr-lod/')
# DBpedia Resources namespace to reference real-world entities
DBR = Namespace('http://dbpedia.org/resource/')
# DBpedia Ontology namespace to describe standard classes and properties (as dbo:Organization, dbo:Place))
DBO = Namespace('http://dbpedia.org/ontology/')

#putting prefixes so the Turtle output shows short names (not full URIs)
g.bind('ex', EX)
g.bind('dbr', DBR)
g.bind('dbo', DBO)
g.bind('dc', DC)
g.bind('dcterms', DCTERMS)
g.bind('foaf', FOAF)
g.bind('skos', SKOS)
g.bind('owl', OWL)

# creating unique URI from string
def uri(seed: str) -> str:
    h = hashlib.md5(seed.encode('utf-8')).hexdigest()
    return "https://polinakhrm.github.io/udhr-lod/" + h # append to the base URI

# building URI for title
title_el = root.find('.//tei:titleStmt/tei:title', ns) #searching title in tei
title_txt = title_el.text.strip() if title_el is not None else 'UDHR'
doc_uri = URIRef(uri(title_txt)) # forming uri adding coded version of title text

# adding document metadata as triples 
g.add((doc_uri, RDF.type, FOAF.Document)) # defining that doc_uri (declaration) is a document (foaf:Document) 
g.add((doc_uri, RDF.type, DBO.Text)) # defining that doc_uri is also a text (dbo:Text)
g.add((doc_uri, DC.title, Literal(title_txt, lang='en'))) # defining doc_uri also in a readable for us manner via literal

# defining publication date via dcterms:date
date_el = root.find('.//tei:publicationStmt/tei:date', ns) # #searching date in tei
if date_el is not None:
    when = date_el.get('when') or date_el.text.strip() # taking the value of attribute 'when' or textual writing of a date
    g.add((doc_uri, DCTERMS.date, Literal(when, datatype=XSD.date))) # defining that doc_uri has the date

# defining publisher via dc:creator and dcterms:publisher
pub_el = root.find('.//tei:publicationStmt/tei:publisher', ns) # searching publisher element in tei
if pub_el is not None and pub_el.text: # checking if the element exists and contains text
    name = pub_el.text.strip().replace(' ', '_') # replacing spaces with underscores (preparing for URI)
    pub  = DBR[name] # building URI with dbr namespace adding name to the end
    g.add((doc_uri, DC.creator, pub)) # defining that doc_uri created by publisher
    g.add((doc_uri, DCTERMS.publisher, pub)) # defining also that doc_uri published by publisher

# Connecting local/internal identification with link to UN website
g.add((doc_uri, OWL.sameAs,
       URIRef('https://www.un.org/en/about-us/universal-declaration-of-human-rights')))

# Monograph imprint details 
mon = root.find('.//tei:sourceDesc/tei:biblStruct/tei:monogr', ns) # searching monograph element in tei
if mon is not None:
    alt = mon.find('tei:title', ns) # revealing if there is alternative name
    if alt is not None and alt.text:
        g.add((doc_uri, DCTERMS.alternative, Literal(alt.text.strip(), lang='en'))) # if exsists adding to graph
    place = mon.find('tei:imprint/tei:pubPlace', ns) #  searching place element in tei
    if place is not None and place.text:
        g.add((doc_uri, DCTERMS.spatial, Literal(place.text.strip(), lang='en'))) # defining that doc_uri has location "Paris"

# defining keywords via skos:Concept and owl:sameAs
for term in root.findall('.//tei:keywords/tei:term', ns): # searching terms elements in tei
    cid  = term.get('xml:id') or term.text.strip() # taking the value of concept's attribute id or just its text
    cURI = URIRef(uri("Concept_" + cid)) # building unique URI 
    lbl  = term.text.strip() # saving readable label
    g.add((cURI, RDF.type, SKOS.Concept)) # defining that concept's URI has the type 'concept'
    g.add((cURI, SKOS.prefLabel, Literal(lbl, lang='en'))) # defining also that concept's URI has label in a readable for us manner via literal
    corr = term.get('corresp') # checking if there is attribute about web-site source
    if corr:
        g.add((cURI, OWL.sameAs, URIRef(corr))) # connecting cocept URI with web-site
    g.add((doc_uri, DCTERMS.subject, cURI)) # defining that document has subject of the concept

# defining organizations via FOAF.Organization and DBO.Organization
for org in root.findall('.//tei:listOrg/tei:org', ns): # searching orgaisations in tei
    same = org.get('sameAs') #taking the value of the attribute 'sameAs'
    name = org.find('tei:orgName', ns).text.strip() # revealing readable for us text name
    if not same:
        continue
    orgURI = URIRef(same) # making the value of sameAs as URIRef
    g.add((orgURI, RDF.type, FOAF.Organization)) # defining that organisation has type of foaf.organisation
    g.add((orgURI, RDF.type, DBO.Organization)) # defining also that organisation has type of dbo.organisation (class from DBpedia ontology)
    g.add((orgURI, FOAF.name, Literal(name, lang='en'))) # defining that organisation has also a name in a readable for us manner via literal
    g.add((doc_uri, DCTERMS.contributor, orgURI)) # defining relation UDHR document has contributor in a face of an organisation 

# defining preamble via ex.section
pre = root.find('.//tei:div[@type="preamble"]', ns) # searching preable in tei
if pre is not None:
    secURI = URIRef(uri("preamble")) # unique URI for preamble
    text = ' '.join(
        chunk.strip()
        for chunk in pre.itertext()
        if chunk.strip()
    ) # iterating all text parts in preable
    g.add((secURI, RDF.type, EX.Section)) # defining preable as section 
    g.add((secURI, EX.sectionText, Literal(text, lang='en'))) # defining that preamble has readable text via literal
    g.add((doc_uri, EX.hasSection, secURI)) # defining that document has section 'preamble'

# defining articles via EX:Article
article_nodes = []
for art in sorted(
        root.findall('.//tei:div[@type="article"]', ns),
        key=lambda x: int(x.get('n') or 0)
    ):
    n = art.get('n') or ''
    artURI = URIRef(uri(f"article{n}"))

    # declare the article type and its number
    g.add((artURI, RDF.type, EX.Article))
    g.add((
        artURI,
        EX.articleNumber,
        Literal(int(n), datatype=XSD.integer)
    ))

    # gather all text inside the article element
    raw_text = ''.join(art.itertext())
    text     = ' '.join(raw_text.split())
    g.add((artURI, EX.articleText, Literal(text, lang='en')))

    # append this article URI to our ordered list
    article_nodes.append(artURI)

# create a blank node and immediately link it to the document
from rdflib.namespace import RDF

seq = BNode()
# link the document and the container
g.add((doc_uri, EX.hasOrderedArticles, seq))
# specify that this is a sequence
g.add((seq, RDF.type, RDF.Seq))

# populate it by passing the article_nodes list
Collection(g, seq, article_nodes)

# populate the rdf:Seq with the ordered list of article URIs
Collection(g, seq, article_nodes)

#serializing the graph 
g.serialize(destination='udhr_output.ttl', format='turtle')
print("udhr_output.ttl")