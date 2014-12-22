patent-analysis-framework
=========================

Proposed framework for extracting and analyzing Patent data using Neo4j and MongoDB.

#Project structures
docs: 
eve:
README.md:
requirements.txt:
src: source code folder

#Installation
To install required modules, please use the following command:
'''pip install -r /path/to/requirements.txt'''

#Usage
##Extract data from XML
You can extract data from XML by using the following command:
'''python parse_patent.py --input=<inputfile.xml> --size=<number_of_xmls> --export=<export_type>'''
######Arguments
'''
inputfile.xml	--	Path to input file
number_of_xmls	--	Number of patents want to parse
export_type		--	File type to export (Till now we just support for json)
'''

##Insert data into database
You can insert data into Neo4j or MongoDB using the following command:
'''python db_client.py '''
This module will get the data from data.json in the working folder and parse directly to database.
Caution: You must start Neo4j and MongoDB server before execute this module, otherwise, it will raise error.

##Generate csv from Neo4j database
You can generate nodes and relationships from Neo4j database into two .csv file by using the following command:
'''python generate_csv.py'''
Caution: You must start Neo4j server first

