
# Let's just use the local mongod instance. Edit as needed.

# Please note that MONGO_HOST and MONGO_PORT could very well be left
# out as they already default to a bare bones local 'mongod' instance.
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_USERNAME = 'lala'
MONGO_PASSWORD = '1234'
MONGO_DBNAME = 'patentdb'
MONGO_QUERY_BLACKLIST = ['$where'] 
# Enable reads (GET), inserts (POST) and DELETE for resources/collections
# (if you omit this line, the API will default to ['GET'] and provide
# read-only access to the endpoint).
RESOURCE_METHODS = ['GET', 'POST', 'DELETE']

# Enable reads (GET), edits (PATCH), replacements (PUT) and deletes of
# individual items  (defaults to read-only item access).
ITEM_METHODS = ['GET', 'PATCH', 'PUT', 'DELETE']


patent_schema = {
    # Schema definition, based on Cerberus grammar. Check the Cerberus project
    # (https://github.com/nicolaiarocci/cerberus) for details.
        'kind': {
            'type':'string'
        }, 
        'date-published': {
            'type':'string'
        }, 
        'number-of-claims': {
            'type':'integer'
        }, 
        'country': {
            'type':'string'
        }, 
        'patid': {
            'type':'string',
            'required':True,
            'unique':True
        },
        'main-classification':{
            'type':'string',
        },
        'title': {
            'type':'string'
        },
        'app-number': {
            'type':'string'
        }, 
        'citations':{
            'type':'list',
            'schema':{
                       'type':'string'
                   }
        },
        'date-produced':{
            'type':'string'
        }, 
        'inventors':{
            'type':'list',
            'schema':{
                'type':'dict',
                'schema':{
                    'city':{
                        'type':'string'
                    }, 
                    'last-name':{
                        'type':'string'
                    }, 
                    'country':{
                        'type':'string'
                    }, 
                    'first-name':{
                        'type':'string'
                    }
                }
            }
        }
    }

inventor_schema={
        'city':{
            'type':'string'
        }, 
        'last-name':{
            'type':'string'
        }, 
        'country':{
            'type':'string'
        }, 
        'first-name':{
            'type':'string'
        }
    
}
inventors = {
    #'item_title': 'inventor',
   # 'additional_lookup': {
  #      'url': 'regex("[\w]+")',
   #     'field': 'first-name'
   # },
    'cache_control': 'max-age=10,must-revalidate',
    'cache_expires': 10,

    # most global settings can be overridden at resource level
    'resource_methods': ['GET', 'POST','DELETE'],

    'schema': inventor_schema
}

patents = {
    # 'title' tag used in item links. Defaults to the resource title minus
    # the final, plural 's' (works fine in most cases but not for 'people')
    'item_title': 'patent',
    # by default the standard item entry point is defined as
    # '/people/<ObjectId>'. We leave it untouched, and we also enable an
    # additional read-only entry point. This way consumers can also perform
    # GET requests at '/people/<lastname>'.
    'additional_lookup': {
         'url': 'regex("[\w]+")',
         'field': "patid"
     },
  
    # We choose to override global cache-control directives for this resource.
    'cache_control': 'max-age=10,must-revalidate',
    'cache_expires': 10,

    # most global settings can be overridden at resource level
    'resource_methods': ['GET', 'POST','DELETE'],
    'item_methods' : ['GET', 'PATCH', 'PUT', 'DELETE'],
    

    'schema': patent_schema
}

DOMAIN = {
    'patents':patents,
    'inventors':inventors
}
