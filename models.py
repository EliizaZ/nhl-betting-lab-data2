import numpy as np

def fair_odds(prob):
    return 1/prob if prob>0 else None

def edge(fair,book):
    return (book-fair)/fair if fair and book else 0

