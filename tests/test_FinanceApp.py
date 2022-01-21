#! python3

import pytest, sys, os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                            os.pardir))
sys.path.append(PROJECT_ROOT)
from FinanceApp import FinanceApp as FA



def test_a(): 
    print('a')
