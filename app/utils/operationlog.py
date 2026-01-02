# from app.models import OperationLog
from app import setup_logger
from functools import wraps
from flask import request
from flask_login import current_user
from app import db
from app.models import OperationLog
import time

logger = setup_logger()

def sanitize_params(params):
    """Recursively sanitize sensitive information in parameters."""
    if isinstance(params, dict):
        sanitized = params.copy()
        for key, value in sanitized.items():
            if isinstance(key, str) and any(sensitive in key.lower() for sensitive in ['password', 'pwd', 'token', 'secret']):
                sanitized[key] = '******'
            else:
                sanitized[key] = sanitize_params(value)
        return sanitized
    elif isinstance(params, list):
        return [sanitize_params(item) for item in params]
    else:
        return params

def log_operation(operation_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Log operation details
            method = request.method
            path = request.path
            
            # Log query parameters
            if method in ['GET', 'DELETE']:
                params = request.args.to_dict()
            else:  # POST/PUT
                params = request.get_json(silent=True) or {}
            
            sanitized_params = sanitize_params(params)
                
            # Log to console
            logger.debug(f"Operation: {operation_name}, Method: {method}, Path: {path}, Params: {sanitized_params}")

            # Save to database
            log_entry = OperationLog(
                OPERATION_NAME=operation_name,
                METHOD=method,
                PATH=path,
                PARAMS=str(sanitized_params),
                OPERATOR = current_user.NAME if current_user and current_user.is_authenticated else 'Anonymous'
            )
            db.session.add(log_entry)
            
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                execution_time = time.time() - start_time
                log_entry.OPERATIONTIME = int(execution_time * 1000)  # Convert to milliseconds
                
                # Check if result is a response object or tuple
                if hasattr(result, 'get_json'):
                    json_msg = result.get_json(silent=True) or {}
                else:
                    json_msg = {} # simple fallback
                    
                logger.debug(f"Execute successful: {json_msg} | Execution time: {execution_time:.2f} ms")
                log_entry.RESULT = 1
                log_entry.RESPONSE = str(json_msg)
            
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                log_entry.OPERATIONTIME = int(execution_time * 1000)
                log_entry.RESULT = 0
                logger.error(f"Execute failed: {e} | Execution time: {execution_time:.2f} ms")
                log_entry.EXCEPTION = str(e)
                db.session.commit()
                raise e
            finally:
                db.session.commit()
                logger.debug(f"Operation log saved: {log_entry}")
        return decorated_function
    return decorator