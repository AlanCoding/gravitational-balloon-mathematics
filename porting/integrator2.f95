! "Gas Giant" planetary physics analysis code
!   Start with some central pressure, then this code integrates
!  the system of differential equations to predict the gas pressure
!  and gravitational field throughout the interior of that planet.
!
!   Intended to produce numbers for the fictional world Virga, with
!  two example cases where the central pressure is 1 atmosphere and
!  then 3 atmospheres. Spatial data is outputed to files.
!   Parameters are also put in place for Jupiter and the sun, but these
!  cases have a problem with spatial resolution near the center.
!  With 10000 spatial points, Jupiter can be resolved to some extent but
!  not the sun.

module gas_values
  double precision, parameter :: G = 6.67384e-11
  double precision :: Rsp = 287.058
  double precision :: T = 293.
end module

program ball
  use gas_values
  implicit none
  double precision :: r, r_max, r_step, rold
  double precision, dimension(2) :: x, xold
  integer :: theunit
  double precision :: kB, amu
  interface
    function Pg(xp,tp)
      implicit none
      double precision, dimension(2), intent(in) :: xp
      double precision, intent(in) :: tp
      double precision, dimension(2) :: Pg
    end function
  end interface
  interface
    function PM(xp,tp)
      implicit none
      double precision, dimension(2), intent(in) :: xp
      double precision, intent(in) :: tp
      double precision, dimension(2) :: PM
    end function
  end interface

  open( unit=2, file="output_1atm.txt", status="replace" )
  open( unit=3, file="output_3atm.txt", status="replace" )
  open( unit=4, file="output_jupiter.txt", status="replace" )
  open( unit=5, file="output_sun.txt", status="replace" )

  r_max = 1.0e8
  r_step = r_max / 10000

  kB = 1.3806488e-23 ! boltzmann constant
  amu = 1.66053892e-27 ! in kg
  write(*,*) ' R specific for air '
  write(*,*) ' using: ',Rsp
  write(*,*) ' calc: ', kB / ( 28.97 * amu )

  ! normal case
  x = (/ 1.0e5, 0.0 /)
  theunit = 2
  r = 100.0
  write(theunit,*) '  radius     pressure     field '
  do
    write(theunit,*) r, x
    xold = x
    call rk4(Pg,xold,x,r,r_step)
    r = r + r_step
    if (r > r_max ) exit
  end do


  ! high pressure case
  x = (/ 3.0e5, 0.0 /)
  theunit = 3
  r = 100.0
  write(theunit,*) '  radius     pressure     field '
  do
    write(theunit,*) r, x
    xold = x
    call rk4(Pg,xold,x,r,r_step)
    r = r + r_step
    if (r > r_max ) exit
  end do

  ! Jupiter case
  Rsp = kB / ( (1.*0.898+4.*0.102+16.04*0.003)* amu )
  write(*,*) ' jupiter Rsp ',Rsp
  x = (/ 1.0e5*100.0e6, 0.0 /) ! 6 million atmospheres at center
  theunit = 4
  r = 100.0
  write(theunit,*) '  radius     pressure     field '
  do
    write(theunit,*) r, x
    xold = x
    call rk4(Pg,xold,x,r,r_step)
    r = r + r_step
    if (r > r_max ) exit
  end do

  ! Sun case
  Rsp = kB / ( (1.*0.912+4.*0.087+16.*0.0097)* amu )
  write(*,*) ' sun Rsp ',Rsp
  x = (/ 1.0e5*2.5e11, 0.0 /)
  T = 5500.
  theunit = 5
  r = 100.0
  write(theunit,*) '  radius     pressure     field '
  do
    write(theunit,*) r, x
    xold = x
    call rk4(Pg,xold,x,r,r_step)
    r = r + r_step
    if (r > r_max ) exit
  end do

  close(2)
  close(3)
  close(4)
  close(5)

end program ball


function PM(x,r)
  use gas_values
  implicit none
  double precision, dimension(2), intent(in) :: x
  double precision, intent(in) :: r
  double precision, dimension(2) :: PM

  PM(1) = (G / (Rsp * T))*(r**2)*x(2)
  PM(2) = -(4. * 3.141592654 / (Rsp * T))*x(1)*x(2)/(r**2)
end function


function Pg(x,r)
  use gas_values
  implicit none
  double precision, dimension(2), intent(in) :: x
  double precision, intent(in) :: r
  double precision, dimension(2) :: Pg

  Pg(1) = -(G / (Rsp * T))*x(2)*x(1)/G
  Pg(2) = (4. * 3.141592654 / (Rsp * T))*G*x(1) - 2*x(2) / r
end function

subroutine rk4(F,x0,x,t0,delt)
  implicit none
  double precision, intent(in) :: x0(2)
  double precision, intent(out) :: x(2)
  double precision, intent(in) :: t0, delt
  double precision :: k1(2), k2(2), k3(2), k4(2)
  interface
    function F(xp,tp)
      implicit none
      double precision, dimension(2), intent(in) :: xp
      double precision, intent(in) :: tp
      double precision, dimension(2) :: F
    end function
  end interface

  k1 = F(x0,t0)
  k2 = F(x0 + k1*delt/(2.0),t0+0.5*delt)
  k3 = F(x0 + k2*delt/(2.0),t0+0.5*delt)
  k4 = F(x0 + k3*delt, t0 + delt)
!   write(*,*) ' k ',k1,k2,k3,k4
  x = x0 + (k1+2*k2+2*k3+k4)*delt/(6.0)

end subroutine rk4
