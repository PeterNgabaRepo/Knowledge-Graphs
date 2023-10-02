#!/usr/bin/env python

""" A simple script to run one or more sparql queries on an endpoint and save the results as json and html. Examples

  python sparql.py https://dbpedia.org/sparql myquery.txt
  python sparql.py q*.txt  

First argument is endpoint if it looks like a URL, remaining args are names of files with SPARQL queries. Sends query in file F to the endpoint and writes results to files F.json and F.html
"""

import codecs 
import sys
import json
from SPARQLWrapper import SPARQLWrapper, JSON

usage = """USAGE: python sparql.py [endpoint] q1file q2file ... qnfile"""

def main():
    """If run as a script, invoke this"""
    if len(sys.argv) < 2:
        sys.exit(usage)
    elif sys.argv[1].lower().startswith('http'):
        endpoint = sys.argv[1]
        files = sys.argv[2:]
    else:
        endpoint = None
        files = sys.argv[1:]
    for file in files:
        if endpoint:
            ask_and_write(file, endpoint)
        else:
            ask_and_write(file, guess_endpoint(file))

# some sparql endpoints
dbpedia_live_endpoint = "http://live.dbpedia.org/sparql"
dbpedia_endpoint = "http://dbpedia.org/sparql"
wikidata_endpoint = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
default_endpoint = wikidata_endpoint

# user agent for http request (required by wikidata query service, change for your info)
USER_AGENT = "UMBC691 (Tim Finin)"

def ask_query(query, endpoint=default_endpoint):
    sparql = SPARQLWrapper(endpoint, agent=USER_AGENT)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    try:
        return sparql.query().convert()        
    except Exception as e:
        print('Error', str(e))
        return None

def number_results (json_obj):
    """ Returns number of results in json object returned by endpoint """
    if not json_obj:
        return 0
    elif 'results' in json_obj: # select query result
        return len(json_obj['results']['bindings'])
    elif 'boolean' in json_obj: # ask query result
        return 1
    else:                      # construct query result
        return len(json_obj)
                  
def json2html(data):
    """ Constructs HTML string from json object returned by sparql query"""
    html = ''
    if 'results' in data and data['head']:
        # json is from a select sparql query
        vars = data['head']['vars']
        html = '<thead><tr>' + ''.join(['<th> %s </th>' % v for v in vars]) + '</tr></thead><tbody>'
        for result in data['results']['bindings']:
            result_values = [linkify(result.get(v,{}).get('value', '')) for v in vars]
            html += '<tr>' + ''.join(['<td>'+ rv + '</td>' for rv in result_values]) + '</tr>'
        html += '</tbody>'
    elif 'boolean' in data:
        # json from ask query
        html = str(data['boolean'])
    else:
        # json is from a construct sparql query
        for (s, po) in data.items():
            for (p, objs) in po.items():
                for o in objs:
                    html += '<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (linkify(s), linkify(p), linkify(o['value']))
    return '<table border="1">' + html + '</table>'

def linkify(string):
    """ if string looks like a URI, turn it into a link """
    result = '<a href="%s">%s</a>' % (string, string) if string.startswith('http://') else string
    #return result.encode('utf-8')
    return result
        
def ask_and_write(file, endpoint):
    print('query {0}: {1} '.format(file, endpoint))
    data = ask_query(open(file).read(), endpoint)
    if data:
        print('Query returned {0} results'.format(number_results(data)))
        with codecs.open(file+".html", 'w', encoding="utf-8") as HOUT:
            HOUT.write("<html><body>"+json2html(data)+"</body></html>")
        with codecs.open(file+".json", 'w', encoding="utf-8") as JOUT:
            JOUT.write(json.dumps(data, indent=1, separators=(',', ':')))
    else:
        print('Query {0} failed'.format(file))
    print('')
        

def guess_endpoint(filename):
    """ Guess the enpoint to send the query to based on its first character"""
    if filename.startswith('w'):
        return wikidata_endpoint
    elif filename.startswith('d'):
        return dbpedia_endpoint
    else:
        return default_endpoint
        
# if invoked as a script, call main()
if __name__ == "__main__":
    main()

