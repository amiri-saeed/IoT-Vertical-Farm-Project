import cherrypy
import json
# import requests


class NotificationServ(object):

    exposed = True
    def __init__(self, bot):
        self.bot = bot

    '''
    GET
    '''
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):

        endpoint = uri[0]

        if endpoint == "notify_user":
            payload = cherrypy.request.json
            response = self.bot.send_notification(params, payload)
        else:
            raise cherrypy.HTTPError(404, "Endpoint not found")

        return response

    '''
    POST, PUT, DELETE
    '''