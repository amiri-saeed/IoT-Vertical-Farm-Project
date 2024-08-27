import cherrypy
import json
# import requests


class Server(object):

    exposed = True # DONT FORGET THIS LINE!!
    def __init__(self, analyzer):
        self.analyzer = analyzer


    '''
    GET
    '''
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):

        response = "ALIVE"

        return response



    '''
    POST, PUT, DELETE
    '''