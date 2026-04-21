import math

# j1  = index to define Emin define the range of electron energies used in the integration
# j2  = index to define Emax define the range of electron energies used in the integration

# j1=1 ; j2=120 corresponds to 0.01 - 10  MeV
# j1=29; j2=160 corresponds to 0.05 - 100 MeV
# j1=41; j2=160 corresponds to 0.10 - 100 MeV
# j1=41; j2=200 corresponds to 0.10 - 1000 MeV


def convertEminToJ1(emin):
    j1 = 1 + (math.log10(emin) + 2) / 0.025    
    return round(j1)

def convertEmaxToJ2(emax):
    j2 = (math.log10(emax) + 2) / 0.025
    return round(j2)
