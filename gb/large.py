# "Gas Giant" planetary physics analysis code
#   Start with some central pressure, then this code integrates
#  the system of differential equations to predict the gas pressure
#  and gravitational field throughout the interior of that planet.
#
#   Intended to produce numbers for the fictional world Virga, with
#  two example cases where the central pressure is 1 atmosphere and
#  then 3 atmospheres. Spatial data is outputed to files.
#   Parameters are also put in place for Jupiter and the sun, but these
#  cases have a problem with spatial resolution near the center.
#  With 10000 spatial points, Jupiter can be resolved to some extent but
#  not the sun.
import json
from math import pi

from .constants import Gval


Rsp = 287.058
T = 293.  # Kelvin
kB = 1.3806488e-23  # boltzmann constant
amu = 1.66053892e-27  # in kg


def main():
  summary = {}

  r_max = 1.0e8
  r_step = r_max / 10000

  print(' R specific for air ')
  print(' using: ' + str(Rsp))
  print(' calc: ' + str(kB / ( 28.97 * amu )))

  # normal case
  x = ( 1.0e5, 0.0 )
  r = 100.0
  data = []
  while True:
    data.append(r + x)
    xold = x
    x = rk4(Pg,xold,r,r_step)
    r = r + r_step
    if (r > r_max ):
      break
  summary['1atm'] = data

  # high pressure case
  x = ( 3.0e5, 0.0 )
  r = 100.0
  data = []
  while True:
    data.append(r + x)
    xold = x
    x = rk4(Pg,xold,r,r_step)
    r = r + r_step
    if (r > r_max ):
        break
  summary['3atm'] = data

  # Jupiter case
  Rsp = kB / ( (1.*0.898+4.*0.102+16.04*0.003)* amu )
  print(' jupiter Rsp ' + str(Rsp))
  x = ( 1.0e5*100.0e6, 0.0 )  # 6 million atmospheres at center
  theunit = 4  # output_jupiter.txt
  r = 100.0
  data = []
  while True:
    data.append(r + x)
    xold = x
    x = rk4(Pg,xold,r,r_step)
    r = r + r_step
    if (r > r_max ):
        break
  summary['jupiter'] = data

  # Sun case
  Rsp = kB / ( (1.*0.912+4.*0.087+16.*0.0097)* amu )
  print(f'  sun Rsp {Rsp}')
  x = ( 1.0e5*2.5e11, 0.0 )
  T = 5500.
  r = 100.0
  data = []
  while True:
    data.append(r + x)
    xold = x
    x = rk4(Pg,xold,r,r_step)
    r = r + r_step
    if (r > r_max ):
        break
  summary['sun'] = data

  print('')
  print('Will show data with colums:')
  print('      radius    pressure    field')
  print(json.dumps(summary, indent=2))


def PM(x, r):
  # double precision, dimension(2), intent(in) :: x
  # double precision, intent(in) :: r
  # double precision, dimension(2) :: PM

  return [
    (Gval / (Rsp * T))*(r**2)*x[1],
    -(4. * pi / (Rsp * T))*x[0]*x[1]/(r**2)
  ]


def Pg(x, r):
  # double precision, dimension(2), intent(in) :: x
  # double precision, intent(in) :: r
  # double precision, dimension(2) :: Pg

  return [
    -(Gval / (Rsp * T))*x[1]*x[0]/Gval,
    (4. * pi / (Rsp * T))*Gval*x[0] - 2*x[1] / r
  ]


def rk4(F,x0,t0,delt):
  # double precision, intent(in) :: x0(2)
  # double precision, intent(out) :: x(2)
  # double precision, intent(in) :: t0, delt
  # double precision :: k1(2), k2(2), k3(2), k4(2)

  k1 = F(x0,t0)
  k2 = F(x0 + k1*delt/(2.0),t0+0.5*delt)
  k3 = F(x0 + k2*delt/(2.0),t0+0.5*delt)
  k4 = F(x0 + k3*delt, t0 + delt)
#   write(*,*) ' k ',k1,k2,k3,k4
  return x0 + (k1+2*k2+2*k3+k4)*delt/(6.0)
