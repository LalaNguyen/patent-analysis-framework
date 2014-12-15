"""
    mongodb-client
    ~~~~~~~~~~~~~~~
    Based on eve-mongodb-client-demo of Nicola, provides more functions to work with
    specific xml 4.5 DTD of US patents. Currently support function:
    
    Public functions:
    - post_patents
    - post_inventors
    - get
    
    Private functions:
    - post
    - delete_all
"""
from eve import Eve
import requests
import json
import settings
import ijson

ENTRY_POINT = 'http://localhost:5000'
FILE_NAME ="data.json"   

           
class MongoDBConnector(object):
    """Create connector to communicate with mongodb via eve.
    
    Public functions:
    - post_patents
    - post_inventors
    - get
    
    Private functions:
    - post
    - delete_all
    """
    
    
    def __init__(self,entry):
        self.entry_point=entry
        
    def _post(self,resource, data):
        """Perform the actual POST.
    
        Args:
            :param resource(str): endpoint of connection. E.g people, inventors
            :param data(list): list of patent data that are parsed from json.
    
        Returns: 
            :param r(dict): json object of the response
        """
        headers = {'Content-Type':'application/json'}
        # Convert list data to json format
        query = json.dumps(data, indent=4)
        return requests.post(self.endpoint(resource),query,headers=headers)
    
    def post(self,data,resource):
        """POST bulk of list, also work with single list.
    
        Args:
            :param data(list): list of patent data that are parsed from json.
            :param resource(str): endpoint of connection. E.g people, inventors
    
        Returns: 
            :param r(dict): json object of the response
            
        """
        r = self._post(resource,data)
        valids = []
        if r.status_code == 201:
            response = r.json()
            if response['_status'] == 'OK':
                for person in response['_items']:
                    if person['_status'] == "OK":
                        valids.append(person['_id'])
        else: 
            print r.json()
        return valids  
          
    def endpoint(self,resource):
        return '%s/%s/' % (self.entry_point, resource)
        
    def perform_get(self,resource):
        """Perform the actual GET.
    
        Args:
            :param resource(str): endpoint of connection. E.g people, inventors
    
        Returns: 
            :param r(dict): json object of the response
        """
        r = requests.get(self.endpoint(resource))
        return r.json()
    
    def get(self,resource):
        """GET an endpoint collection.
    
        Args:
            :param resource(str): endpoint of connection. E.g people, inventors
    
        Returns: 
            :param r(dict): json object of the response
            
        """
        r = self.perform_get(resource)
        return r
    
    def _delete_all(self,resource):
        """Perform the actual DELETE.
    
        Args:
            :param resource(str): endpoint of connection to be deleted. E.g people, inventors
    
        Returns: 
            :param r(dict): json object of the response
        """
        r = requests.delete(self.endpoint(resource))
        return r
        
if __name__ == '__main__':
    # Initiate Connector
    client=MongoDBConnector(ENTRY_POINT)
    data=[]
    inventors=[]
    # Open file to read
    with open(FILE_NAME) as file:
        # Parse json file to Element Tree
        objects = ijson.items(file,'item')
        # Build up our list data to post from
        for o in objects:
            data.append(o)
            inventors.extend(o["inventors"])
            
        # Example APIs
        r = client.post(data=data,resource="patents")  
        i = client.post(data=inventors,resource="inventors")
        dp = client._delete_all("patents")
        di = client._delete_all("inventors")
        g = client.get("inventors")