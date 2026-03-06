#utils/errors.py
"""Define custom error handlers for application."""
from flask import jsonify, make_response, render_template
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
    error_items = [item.strip() for item in str(error).split(';') if item.strip()]
    if not error_items:
        error_items = ["Si e' verificato un errore durante l'elaborazione dei file caricati."]

    return make_response(
        render_template(
            'error.html',
            status_code=400,
            title="Impossibile completare il report",
            subtitle="I file caricati contengono dati da correggere. Nessun punteggio e' stato calcolato.",
            error_items=error_items,
        ),
        400,
    )
