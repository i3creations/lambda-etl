"""
HTML Stripper Module

This module provides functionality to strip HTML tags from text.
It contains a custom HTMLParser subclass (MLStripper) and a utility function (strip_tags).
"""

from io import StringIO
from html.parser import HTMLParser


class MLStripper(HTMLParser):
    """
    A custom HTML parser that strips HTML tags from text.
    
    This class extends HTMLParser to extract only the text content from HTML,
    removing all tags and their attributes.
    """
    
    def __init__(self):
        """Initialize the HTML parser with appropriate settings."""
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()
        
    def handle_data(self, d):
        """Handle text data by writing it to the output buffer."""
        self.text.write(d)
        
    def get_data(self):
        """Get the accumulated text data."""
        return self.text.getvalue()


def strip_tags(html):
    """
    Strip HTML tags from the input text.
    
    Args:
        html (str): HTML text to be stripped of tags
        
    Returns:
        str: Text content without HTML tags
        
    Example:
        >>> strip_tags("<p>Hello <b>World</b>!</p>")
        'Hello World!'
    """
    if not html:
        return ""
    s = MLStripper()
    s.feed(html)
    return s.get_data()
