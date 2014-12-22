#!flask/bin/python

from eve import Eve
from flask.ext.bootstrap import Bootstrap


if __name__ == '__main__':
    app = Eve()
    app.run(debug=True)