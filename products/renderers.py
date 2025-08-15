import json
from rest_framework.renderers import JSONRenderer
from django.core.serializers.json import DjangoJSONEncoder

class UnicodeJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer that ensures proper Unicode handling for Arabic text.
    This renderer disables ASCII encoding to properly display Arabic characters.
    """
    media_type = 'application/json'
    charset = 'utf-8'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, returning a bytestring.
        """
        if data is None:
            return b''

        renderer_context = renderer_context or {}
        indent = self.get_indent(accepted_media_type, renderer_context)

        if indent is None:
            separators = (',', ':')
        else:
            separators = (',', ': ')

        ret = json.dumps(
            data, 
            cls=DjangoJSONEncoder,
            indent=indent, 
            separators=separators,
            ensure_ascii=False  # This is the key change for Arabic text
        )
        
        # Return bytes, encoded as UTF-8
        return ret.encode('utf-8')