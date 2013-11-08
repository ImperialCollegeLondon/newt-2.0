from newt.views import JSONRestView
from newt.common.response import json_response
from django.http import HttpResponse, HttpResponseServerError, StreamingHttpResponse
from django.conf import settings

file_adapter = __import__(settings.NEWT_CONFIG['ADAPTERS']['FILE'], globals(), locals(), ['adapter'], -1)


import logging


logger = logging.getLogger(__name__)


class FileView(JSONRestView):
    def get(self, request, machine_name, path):
        logger.debug("Entering %s:%s" % (self.__class__.__name__, __name__))

        # File vs. directory
        if request.GET.get('download', 'false')=='true':
            try:
                file_handle = file_adapter.get(machine_name, path)
                # Introspect the contents for mime_type from buffer
                content_type = file_adapter.get_mime_type(machine_name, path, file_handle)
                return StreamingHttpResponse(file_handle, content_type=content_type)
            except Exception as e:
                logger.error("Could not get file %s" % str(e))
                response = json_response(status="ERROR", status_code=500, error="Could not get file: %s" % str(e))            
        else:
            try:
                output, error, retcode = file_adapter.get_dir(machine_name, path)
                if retcode!=0:
                    response = json_response(content=output, status="ERROR", status_code=500, error=error)
                else:
                    response = output
            except Exception as e:
                logger.error("Could not get directory %s" % str(e))
                response = json_response(status="ERROR", status_code=500, error="Could not get directory: %s" % str(e))
            
        return response
        
        
    def put(self, request, machine_name, path):
        logger.debug("Entering %s:%s" % (self.__class__.__name__, __name__))
        
        try:
            response = file_adapter.put(request, machine_name, path)
        except Exception as e:
            logger.error("Could not put file %s" % str(e))
            response = json_response(status="ERROR", status_code=500, error="Could not put file: %s" % str(e))
        
        return response