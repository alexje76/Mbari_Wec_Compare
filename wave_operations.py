"""
Wave Properties Calculator

This module contains functions that are used to calculate various wave properties
"""
import numpy as np

def wavenum(period,depth,tolerance=1e-6,max_iterations=10):
    """
    Linear dispersion relation wavenumber solver.
    k = wavenum(period,depth)
    Solves for the wave-numbers 'k' for a given depth that satisfy the
    dispersion relation: omega^2 = g*k*tanh(k*depth) using the
    Newton-Raphson method.

        Modified from script created on Fri Apr 2 08:05:26 2021
        @author: sdbrenner
    """
    import numpy as np
    #convert period to angular frequency
    omega = 2*np.pi/period

    g = 9.81
    # initial guess based on Fenton and McKee, 1990:
    k0 = omega**2/g
    kn = k0* ( np.tanh((k0*depth)**(3/4)) )**(-2/3)
    converged = 0 #convergence flag
    # iterate with a Newton-Raphson method:
    for n in range(max_iterations):
        err = np.abs( omega**2 - g*kn*np.tanh(kn*depth) )
        if err<tolerance: #pre-debug: if all(err<tolerance):
            converged = 1
            break
        fkn = g*kn*np.tanh(kn*depth) - omega**2
        dfkn = g*np.tanh(kn*depth) + g*depth*kn/np.cosh(kn*depth)**2
        kn = kn - fkn/dfkn
    if converged == 0:
        print('did not converge')
    return kn

def main():
    kn = wavenum(4,5)
    print(kn)
    kn2 = wavenum(12,10)
    print(kn2)
    kn3 = wavenum(8,100)
    print(kn3)
    kn4 = wavenum(16,4000)
    print(kn4)


if __name__ == '__main__':
    main()