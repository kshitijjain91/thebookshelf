
#!/usr/bin/python
import sys
import logging

activate_this = '/var/www/venv3/bin/activate_this.py'
exec(open(activate_this).read(), dict(__file__=activate_this))

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/thebookshelf/")

from thebookshelf import app as application
application.secret_key = 'your secretcnjanclksdvmdvm keybc sjcnjlwnc'



