"""
initializes the logging subsystem for this application
"""
import os
import logging

if len(logging.getLogger().handlers) == 0:
    logging.basicConfig(
        format="%(levelname)s: %(message)s", level=os.getenv("LOG_LEVEL", "INFO")
    )
log = logging.getLogger("aws-route53-ctl")
log.setLevel(os.getenv("LOG_LEVEL", "INFO"))
