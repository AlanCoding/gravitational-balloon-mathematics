' Rotating gravity balloon functions
Function fba(ba As Double)
  Dim e As Double
  e = (1 - ba ^ 2) ^ (1 / 2)
  fba = 2 * Pi() * (1 + 1 / 2 * ba ^ 2 / e * (Log((1 + e) / (1 - e))))
End Function
Function I_RM(R As Double, M As Double, rho As Double) As Double
  Dim T As Double ' Same equation as Wikipedia 2/5 m [(r2^5-r1^5)/(r2^3-r1^3)]
  T = ((3 * M / (4 * Pi() * rho)) + R ^ 3) ^ (1 / 3) - R
  I_RM = 2 / 5 * M * ((R + T) ^ 3 * (R + T) ^ 2 - R ^ 3 * R ^ 2) / ((R + T) ^ 3 - R ^ 3)
End Function

Function P_Mbw(M As Double, b As Double, omega As Double, rho As Double)
  Dim a As Double, T As Double
  a = b / (1 - 1 / 2 * b * omega ^ 2 / (Gval() * M))
  T = M / (rho * a ^ 2 * fba(b / a))
  P_Mbw = 1 / 2 * rho * Gval() * M * T / b ^ 2
End Function

Function I_Mbw(M As Double, b As Double, omega As Double, rho As Double)
  Dim a As Double, T As Double
  a = b / (1 - 1 / 2 * b * omega ^ 2 / (Gval() * M))
  I_Mbw = 2 / 3 * M * a ^ 2
End Function
Function b_Mw(M As Double, omega As Double, rho As Double) As Double
  Dim f2 As Double
  f2 = -15 / 16 * omega ^ 2 / (Gval() * rho * Pi())
  b_Mw = (M / (rho * 4 / 3 * Pi() * (f2 + 1) ^ 2)) ^ (1 / 3)
End Function

Function Pratio_w(omega As Double, rho As Double) As Double
  Dim f2 As Double, f As Double
  f2 = 15 / 16 * omega ^ 2 / (Gval() * rho * Pi())
  f = f2 / (1 + f2)
  Pratio_w = (1 - 6 / 5 * f) * (f2 + 1) ^ (2 / 3)
End Function

Function P_Mw(M As Double, omega As Double, rho As Double) As Double
  Dim b As Double, f2 As Double, f As Double
  b = b_Mw(M, omega, rho)
  f2 = -15 / 16 * omega ^ 2 / (Gval() * rho * Pi())
  f = f2 / (1 + f2)
  P_Mw = 1 / 2 * rho * Gval() * M / b * (1 - 6 / 5 * f)
End Function

Function I_Mw(M As Double, omega As Double, rho As Double) As Double
  Dim f2 As Double, b As Double, a As Double
  f2 = -15 / 16 * omega ^ 2 / (Gval() * rho * Pi())
  b = (M / (rho * 4 / 3 * Pi() * (f2 + 1) ^ 2)) ^ (1 / 3)
  a = b * (f2 + 1)
  I_Mw = 5 / 2 * M * a ^ 2
End Function

Function w_ML(M As Double, L As Double, rho As Double) As Double
  Dim a As Double, b As Double, c As Double, Fa As Double, Fb As Double, n As Integer
  a = 0
  b = 2 * Pi() / (2 * 3600)
  n = 0
  Do
    n = n + 1
    c = (a + b) / 2
    Fc = L_Mw(M, c, rho) - L
    Fa = L_Mw(M, a, rho) - L
    If (Fc = 0 Or (b - a) / 2 < 0.0001) Then
      Exit Do
    Else
      If (Fc * Fa > 0) Then
        a = c
      Else
        b = c
      End If
    End If
    w_ML = c
    If (n > 100) Then
      w_ML = -2
      Exit Do
    End If
  Loop
End Function

Function w_MbL(M As Double, b2 As Double, L As Double, rho As Double) As Double
  Dim a As Double, b As Double, c As Double, Fa As Double, Fb As Double, n As Integer
  a = 0
  b = 2 * Pi() / (2 * 3600)
  n = 0
  Do
    n = n + 1
    c = (a + b) / 2
    Fc = c * I_Mbw(M, b2, c, rho) - L
    Fa = a * I_Mbw(M, b2, a, rho) - L
    If (Fc = 0 Or (b - a) / 2 < 0.0001) Then
      Exit Do
    Else
      If (Fc * Fa > 0) Then
        a = c
      Else
        b = c
      End If
    End If
    w_MbL = c
    If (n > 100) Then
      w_MbL = -2
      Exit Do
    End If
  Loop
End Function
