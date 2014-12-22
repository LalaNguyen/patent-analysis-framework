import sys
import getopt
from lxml import etree
import time

#Code for MongoDB
#from pymongo import MongoClient
#client = MongoClient()

#Code for neo4j DB
from py2neo import Graph
graph_db = Graph()
from py2neo.packages.httpstream import http
http.socket_timeout = 9999

#This function splits the whole xml file into patents by using the "<?xml" tag
def xmlSplitter(data,separator=lambda x: x.startswith('<?xml')):
  buff = []
  for line in data:
    if separator(line):
      if buff:
        yield ''.join(buff)
        buff[:] = []
    buff.append(line)
  yield ''.join(buff)

#Main function
def main(argv):
	inputfile = 'ipg140107.xml'
	outputfile = 'xmlParser_result.txt'
	size = 5000
	parse = False
	try:
		opts, args = getopt.getopt(argv,"hi:s:o:p",["input=","size=","output=","help","parse"])
		if opts ==[]:
			print '[Usage:] xmlParser.py -i=<inputfile.xml> -o=<outputfile> -s=<number_of_xmls> -p'
			sys.exit(2)
	except getopt.GetoptError:
		print '[Usage:] xmlParser.py -i=<inputfile.xml> -o=<outputfile> -s=<number_of_xmls> -p'
		sys.exit(2)
	for opt,arg in opts:
		if opt == '-h':
			print '[Usage:] xmlParser.py -i=<inputfile.xml> -o=<outputfile> -s=<number_of_xmls> -p'
			sys.exit(2)
		elif opt in ("-i","--input"):
			inputfile = arg
		elif opt in ("-s","--size"):
			size=arg
		elif opt in ("-o","--output"):
			outputfile = arg
		elif opt in ("-p","--parse"):
			parse = True
	parse_xml(inputfile,outputfile,size,parse)
    
def parse_xml(infile,outfile,size,parse):
	start = time.time()
	count = 0
	for item in xmlSplitter(open(infile)):
		count += 1
		if count > int(size):
			break
		doc = etree.XML(item)
  
		#Parsing essential data from XML patent  
		fname = doc.xpath('//inventor/addressbook/first-name/text()')
		lname = doc.xpath('//inventor/addressbook/last-name/text()')
		city = doc.xpath('//inventor/addressbook/address/city/text()')
		country = doc.xpath('//inventor/addressbook/address/country/text()')
		doc_number = doc.xpath('//publication-reference/document-id/doc-number/text()')
		if doc_number: doc_number = doc_number[0]
		invention_title = doc.xpath('//invention-title/text()')
		if invention_title: invention_title = invention_title[0]
		kind = doc.xpath('//publication-reference/document-id/kind/text()')
		if kind: kind = kind[0]
		date_publ = doc.xpath('//publication-reference/document-id/date/text()')
		if date_publ: date_publ = date_publ[0]
		citation = doc.xpath('//us-citation/patcit/document-id/doc-number/text()')
	
		if(parse):
			#Create or merge Patent and Inventor into Neo4j DB
			tx = graph_db.cypher.begin()
			for i in range(len(fname)):
				statement =  "MERGE (a:Inventor {first_name:{fname},last_name:{lname}, city:{city}, country:{country}})\
							MERGE (b:Patent{doc_number:{doc_number},invention_title:{invention_title},kind:{kind},date_publ:{date_publ}})\
							MERGE (a)-[:INVENT]->(b)\n"
				tx.append(statement,{"fname":fname[i],"lname":lname[i],"city":city[i],"country":country[i],\
					"doc_number":doc_number,"invention_title":invention_title,"kind":kind,"date_publ":date_publ})
			for i in range(len(citation)):
				statement =  "MERGE (c:Patent {doc_number:{citation_number}})\
							MERGE (d:Patent{doc_number:{doc_number}})\
							MERGE (c)-[:CITEDBY]->(d)\n"
				tx.append(statement,{"citation_number":citation[i],"doc_number":doc_number})
			tx.commit()
		#print "{0}\t{1}".format(count,size)
		#Create Patent and Inventor into MongoDB	
	
	end = time.time()
	#print end-start
	#print 'writing to file {0}'.format(outfile)
	fo = open(outfile,"a")
	str = "{0},\t{1:.3f},\t{2}\n".format(size,end-start,int(parse))
	fo.write(str)
	fo.close()

if __name__ == "__main__":
   main(sys.argv[1:])