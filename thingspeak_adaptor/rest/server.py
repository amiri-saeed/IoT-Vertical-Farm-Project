import cherrypy
import json
import requests




class WebServ(object):

    exposed = True # DONT FORGET THIS LINE !!
    def __init__(self, manager):
        self.tsm = manager


    '''
    GET
    '''
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def GET(self,*uri,**params):
        endpoint = uri[0]
        if endpoint == "retrieve":
            response = self.serve_retrieve(params)
        else:
            raise cherrypy.HTTPError(404, "Endpoint not found")

        return response


    def feeds_filtered(self, feeds):
        filtered_list = list()
        for feed in feeds:
            filtered = {}
            for key, value in feed.items():
                if "field" in key and value is not None:
                    filtered["value"] = value
                    filtered["time"] = feed["created_at"]

            if len(list(filtered)) > 0:
                filtered_list.append(filtered)

        results = {"feeds": filtered_list}
        return results


    def serve_retrieve(self, params):

        translated = self.tsm.translate_params_retrieve(params)

        channel_id = translated["required"]["channel_id"]
        field_num = translated["required"]["field_num"]
        results = translated["optional"]["results"]
        start = translated["optional"]["start"]
        end = translated["optional"]["end"]

        for endpoint in self.tsm.conf["endpoints"]:
            if endpoint["name"] == "read_data":
                url = endpoint["url"].format(channel_id, field_num, results, start, end)
                resp = requests.get(url).json()["feeds"]
                feeds = self.feeds_filtered(resp)

        return feeds



    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def DELETE(self, *uri, **params):
        endpoint = uri[0]
        if endpoint == "clear":
            response = self.serve_clear(params)
        else:
            raise cherrypy.HTTPError(404, "Endpoint not found")

        return response


    def serve_clear(self, params):

        translated = self.tsm.translate_params_clear(params)

        return translated


    '''
    POST, PUT
    '''