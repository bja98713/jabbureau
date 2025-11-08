import os
import base64
import mimetypes
from django import template

register = template.Library()

@register.filter
def as_data_uri(image_field):
    """Return image file content as data URI (base64) for embedding in PDFs.

    Safely handles missing files. If mime type can't be detected defaults to image/jpeg.
    Usage: {{ p.image|as_data_uri }}
    """
    try:
        if not image_field:
            return ''
        # Accept ImageField-like objects or absolute path strings
        path = getattr(image_field, 'path', None)
        if not path and isinstance(image_field, str):
            path = image_field if os.path.isabs(image_field) else None
        if not path or not os.path.exists(path):
            return ''
        mime, _ = mimetypes.guess_type(path)
        if not mime:
            mime = 'image/jpeg'
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        return f'data:{mime};base64,{b64}'
    except Exception:
        return ''

@register.filter
def as_data_uri_path(path: str | None):
    """Return file content for an absolute path as data URI (base64).

    Usage: {{ absolute_path|as_data_uri_path }}
    """
    try:
        if not path or not os.path.exists(path):
            return ''
        mime, _ = mimetypes.guess_type(path)
        if not mime:
            mime = 'image/png'
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        return f'data:{mime};base64,{b64}'
    except Exception:
        return ''
