
from math import exp,log

"""
b: steepness - decreasing <=> b > 0
c: horizontal scale
d: vertical scale
e: inflection point
f: more steepness?
"""

# Log-logistic

def LLogi(x,e,b,c=0,d=1,f=1): # cumulative
    return c + ((d-c) / (1+ exp(b*(log(x)-log(e))))**f)

def llogi(x,e,b,c=0,d=1,f=1): # density
    return ((b/e)*(x/e)**(b-1)) / (1+ (x/e)**b)**2

def llogi_mode(e,b,c=0,d=1,f=1): # max
    return e*((b-1)/(b+1))**(1/b)


# Weibull

def Weibull(x,e,b,c=0,d=1,f=1): # cumulative
    if x < 0: return 0
    else: return 1-exp(-(x/e)**b)

def weibull(x,e,b,c=0,d=1,f=1): # density
    if x < 0: return 0
    else: return (b/e) * (x/e)**(b-1) * exp(-(x/e)**b)

def weibull_mode(x,e,b,c=0,d=1,f=1): # max
    if b==1: return 0
    else: return e*((b-1)/b)**(1/b)


#------------------------------------------------------#
# This code was written by Julien Delafontaine         #
# Bioinformatics and Biostatistics Core Facility, EPFL #
# http://bbcf.epfl.ch/                                 #
# webmaster.bbcf@epfl.ch                               #
#------------------------------------------------------#
