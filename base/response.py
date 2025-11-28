from rest_framework import status
from rest_framework.response import Response


class APIResponse(Response):
    
    def __init__(self, data=None, status=status.HTTP_200_OK, **kwargs):
        super().__init__(data=data, status=status, **kwargs)

