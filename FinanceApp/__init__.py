from flask import Flask

app = Flask(__name__)

from FinanceApp import routes
