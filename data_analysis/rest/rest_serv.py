import cherrypy
import json
# import requests


class AnalysisServ(object):

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

        endpoint = uri[0]

        if endpoint == "average":
            response = self.analyzer.serve_avg(params)
        
        elif endpoint == "max":
            response = self.analyzer.serve_max(params)
        
        elif endpoint == "min":
            response = self.analyzer.serve_min(params)
        
        elif endpoint == "plot":
            response = self.analyzer.serve_plt(params)

        elif endpoint == "plot_compare_shelf":
            response = self.analyzer.serve_comp_plt_shlv(params)

        elif endpoint == "plot_compare_shelves":
            response = self.analyzer.serve_comp_plt_shlvs(params)


        else:
            raise cherrypy.HTTPError(404, "Endpoint not found")

        return response




    '''
    POST, PUT, DELETE
    '''