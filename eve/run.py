#!flask/bin/python

from eve import Eve
from flask.ext.bootstrap import Bootstrap


def before_inserting_item(items):
    print 'Insert', len(items)

if __name__ == '__main__':
    app = Eve()
    app.on_insert_patents  += before_inserting_item
    app.run(debug=True)