import re

from django.utils.html import strip_tags
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class AbstractAPIView(APIView):
    
    def get_bool_query_value(self, param_str):
        value = self.request.GET.get(param_str)
        if value == 'false' or value == 'False' or not value:
            return False
        return True
    
    def get_bool_value_from_string(self, value):
        if value == 'false' or value == 'False' or not value:
            return False
        return True
    
    def get_sanitized_string(self, data_string, is_param_str=False):
        start_url_pattern = r'(?:http://\S+|https://\S+|www\.\S+)'
        end_url_pattern = r'\S+(?:\.com|\.org|\.net|\.gov|\.edu|\.mil|\.int|\.uk|\.ca|\.au|\.in|\.de|\.jp|\.fr|\.it|' \
                          r'\.es|\.nl|\.se|\.no|\.dk|\.br|\.ru|\.cn|\.kr|\.sg|\.hk|\.tw|\.io|\.me|\.info|\.biz|' \
                          r'\.coop|\.museum|\.aero|\.name)'
        match_symbol_pattern = r'[\{\}\[\]\(\)://<>]'
        
        if is_param_str:
            string = self.request.GET.get(data_string)
        else:
            string = self.request.data.get(data_string)
        
        if string:
            string = strip_tags(string)
            string = re.sub(start_url_pattern, '', string)
            string = re.sub(end_url_pattern, '', string)
            string = re.sub(match_symbol_pattern, '', string)
            string = string.strip()
            return string
        
        return None


class HealthCheckAPIView(AbstractAPIView):
    permission_classes = (AllowAny,)
    
    def get(self, request, *args, **kwargs):
        return Response(
            data={"status": "healthy", "service": "product-importer"},
            status=status.HTTP_200_OK
        )
