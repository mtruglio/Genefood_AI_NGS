#utils/errors.py
"""Define custom error handlers for application."""
from flask import jsonify, make_response
from werkzeug.http import HTTP_STATUS_CODES

class ValidationError(Exception):
    def __init__(self, msg):
        self.msg = msg
        
def gen_error(error, status_code, status=None, msg=None):
    """Generate error message format for error handlers."""
   
    message = str(error) or msg
    res = jsonify(status=status,
                  data={"msg": f"{HTTP_STATUS_CODES[status_code]}. {message}"})
    return make_response(res, status_code)
def handle_server_errors(error):
    """Handle all 500 server errors in code."""
    return gen_error(error, 500, "Server error: We are working to"
                     " resolve this issue.")

def handle_404_errors(error):
    """Handle wrong url requests with custom message."""
    status = "error" if isinstance(error, KeyError) else "fail"
    return gen_error(error, 404, status=status)
    
def handle_400_errors(error):
    """Handle 400 errors in resources."""
    message = "Error(s):<br>"+'<br>'.join(str(error).split(';'))
    return message
