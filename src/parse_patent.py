#!/usr/bin/env python

"""
    parse-patent
    ~~~~~~~~~~~~~~~
    Work with specific xml 4.5 DTD of US patent
"""

import cStringIO
import sys, getopt
import xml.sax
import json
import copy
import re
from benchmark import BenchMark

#Define settings and global variables
NEO4J_URL = "http://localhost:7474/db/data"
MAX_NUMBER_OF_PATENTS = True  
class PatentHandler(xml.sax.ContentHandler):
    """Patent Handler creates a handler to hold formatted data that are parsed from xml file.   
    Current captured XML tags:   
    <us-patent-grant>
    <date-publ>
    <file>
    <country>
    <publication-reference>
    <doc-number>
    <kind>
    <inventor>
    <invention-title>
    <number_of_claims>
    <us-references-cited>
        
    """
    def __init__(self):
        self.CurrentData = ""
        self.date_produced = ""
        self.country = ""
        self.date_publ = ""
        self.invention_title = ""
        self.application_number = ""
        self.number_of_claims = ""
        self.doc_number = ""
        self.main_classification = ""
        self.kind = ""
        self.citation_list = []
        self.inventor_list = []
        self.ignore_dict = {
            "inventor":[
                "addressbook",
                "address",
                "state",
                "inventor"
            ],
            "patcit":[
                "classification-national",
                "us-citation",
                "kind",
                "name",
                "date", 
                "patcit", 
                "category",
                "main-classification", 
                "country",
                "classification-cpc-text",
                "document-id"
            ]
        }
        
        # Use stack to store opening tag and its value
        self.stack ={}
        self.enable_stack =False
   
    # Call when an element starts
    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "us-patent-grant":
            self.date_produced = attributes["date-produced"]
            self.date_publ = attributes["date-publ"]
            self.application_number = attributes["file"]
            self.country = attributes["country"]
        if tag == "publication-reference" or tag == "patcit" or tag == "inventor" or tag == "number-of-claims":
            #We found what we want, set our stack ready
            self.enable_stack = True
        if tag == "classification-locarno" :
            self.enable_stack = True
        if tag == "nplcit" :
            self.enable_stack = False
    # Call when a character is read
    def characters(self, content):
        # For tags which occur only once in the xml instance 
        if self.CurrentData == "invention-title":
            if content != '\n':
                self.invention_title = content
        #For tags which occurs many times in the instance or nested, 
        #we use stack. Stack only stores opening tag and value, 
        #just ignore the closing tag            
        if self.enable_stack:
            #if self.CurrentData not in self.stack:
            if content != '\n':
                # Remove special characters
                self.stack[self.CurrentData] = re.sub('[/ -.]','', content.encode('UTF-8','replace'))
                if self.CurrentData == "main-classification":
                    self.stack[self.CurrentData] = content
    # Call when an element ends
    def endElement(self, tag):
        self.CurrentData = tag   
        #End of desired tag, let's close our stack.
        if tag == "publication-reference":
            self.enable_stack = False
            # assign doc-number and kind before clearing stack
            self.doc_number = self.stack['doc-number']
            self.kind = self.stack['kind']
            self.stack.clear() 
        if tag == "inventor":
            for i in self.ignore_dict["inventor"]:
                if i in self.stack:
                    self.stack.pop(i)
            self.inventor_list.append(self.stack.copy())
            self.stack.clear()   
        # Once end of tag us-citation, clear the citation list
        if tag == "patcit":
            for i in self.ignore_dict["patcit"]:
                if i in self.stack:
                    self.stack.pop(i)
            # insert list back to dictionary
            self.citation_list.append(self.stack.copy())
            self.stack.clear()
        if tag == "us-references-cited":
            self.enable_stack = False
            self.stack.clear()           
    
        #Meet end tag of classification-national, clear stack
        if tag == "invention-title":
            self.enable_stack = False
            #print self.stack
            # if this is D patent, we must be able to place stack in classification-locarno
            if "main-classification" in self.stack:
                self.main_classification = self.stack["main-classification"]
            # If this is RE & PP do something else
            self.stack.clear()
        if tag == "number-of-claims":
            self.enable_stack = False
            self.number_of_claims = self.stack["number-of-claims"]
            self.stack.clear()
    # Reset everything to initial state.
    def reset(self):
        self.inventor_list[:] = []
        self.citation_list[:] = []
        self.stack.clear()
        self.inventor_count = 0
        self.citation_count = 0
    
    # Construct Json to work with various database format    
    def serialization(self):
        results = {}        
        results["patid"] = (self.doc_number.encode('UTF-8','replace'))
        results["title"] = self.invention_title.encode('UTF-8','replace')
        results["date-produced"] = self.date_produced.encode('UTF-8','replace')
        results["country"] = self.country.encode('UTF-8','replace')
        results["date-published"] = self.date_publ.encode('UTF-8','replace')
        results["app-number"] = self.application_number.encode('UTF-8','replace')
        results["number-of-claims"] = self.number_of_claims.encode('UTF-8','replace')
        results["kind"] = self.kind.encode('UTF-8','replace')
        results["inventors"] = self.inventor_list
        results["citations"] = self.citation_list
        results["main-classification"]=self.main_classification
        return results
        

def xml_documents(file_obj):
    """Split large xml file into separated xml instance
    
    Args:
        :param file_obj(file_object): a handler to large xml file.
    
    Returns: 
        :param document(str): document form of each xml instance.
        
    """
    document = []
    for line in file_obj:
        if line.strip().startswith('<?xml') and document:
                yield ''.join(document)
                document = []
        document.append(line)
    if document:
        yield ''.join(document)

   
def parse_xml(file_name, size = 0, method = "json"):
    """Parse single XML file into the separated XML instances.
    
    Args:
        :param file_name(str): Name of file within same level as root.
        :param size(int): Number of XML instances within XML file to be read.
        :param method(str): Export method(Default:Json).
    
    Returns: 
    int.  The return code::

             0 -- Success!
    """
    # Set initial values
    count = 0
    results = []
    # add benchmark
    bm = BenchMark()
    global MAX_NUMBER_OF_PATENTS  
    # create an XML Reader
    parser = xml.sax.make_parser()
    # turn off namespaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    # turn off validation for DTD
    parser.setFeature(xml.sax.handler.feature_external_ges, False)
    # override the default Context Handler
    xml_patent_handler = PatentHandler()
    parser.setContentHandler(xml_patent_handler)
    try:
        with open(file_name) as citation:
            bm.toggleOn('Start processing [ ]')
            for xml_part in xml_documents(citation):
                # Cast string back to file-like object to parse
                parser.parse(cStringIO.StringIO(xml_part))
                results.append(copy.deepcopy(xml_patent_handler.serialization()))   
                count = count+1
                if not MAX_NUMBER_OF_PATENTS:
                    if count == int(size):
                        break  
                # Clean up stack after processing one xml paragraph
                xml_patent_handler.reset()
                bm.add(0)
         
        bm.toggleOff(' \bOK] - '+ str(count) + ' patents ')
        if method == "json":
            export2json(results)
        return 0
                       
    except IOError as e:
        raise e
        
def export2json(data):
    """Export to json file
    
    Args:
        :param data(list): data list to be exported.
        
    Returns: 
    int.  The return code::

             0 -- Success!
    """
    bm = BenchMark()
    bm.toggleOn('Dumping to json [ ]')
    with open('data.json', 'w') as outfile:
        json.dump(data, outfile, indent=4, ensure_ascii=False)
        bm.toggleOff('\bOK] - saved to data.json')
    return 0

def main(argv):
    # define local variables
    inputfile = 0
    size = 0
    method = ""
    global MAX_NUMBER_OF_PATENTS
    try:
        opts, args = getopt.getopt(argv,"hi:",["input=","size=","export=","help"])        
        #Empty input, raise error
        if opts == []:
            print '[Usage:] parse_patent.py --i=<inputfile.xml> --s=<number_of_xmls> --e=<export_type>'
            sys.exit(2)
    except getopt.GetoptError:
        print '[Usage:] parse_patent.py --i=<inputfile.xml> --s=<number_of_xmls> --e=<export_type>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '--help':
            print '[Example Usage] ./parse_patent.py \n\
            --input=/path/to/data.xml  # Specify path to data for processing\n\
            --size=1                   # Number of xml instances to be processed\n\
            --export=json              # Support json\n' 
            sys.exit()
        elif opt in ("--input, -i"):
            inputfile = arg
        elif opt in ("--size", "-s"):
            size = arg
            MAX_NUMBER_OF_PATENTS = False
        elif opt in ("--export", "-e"):
            method = arg
    parse_xml(inputfile,size, method)
        
if __name__ == "__main__":
    main(sys.argv[1:])        