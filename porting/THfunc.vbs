' Thermal hydraulic functions
Function c_f(Re As Double) As Double
  Dim f_min As Double, f_max As Double, f As Double
  Dim g_lower As Double, g_middle As Double
  Dim b As Double, kappa As Double
  Dim n As Integer
  b = -0.05
  kappa = 0.41
  f_min = Exp(-2 * b * kappa - Log(Re ^ 2 / 2))
  f_max = ((Log(10) + 1) / (2 * Log(Re / 2.51))) ^ 2
  n = 0
  
  Do
    n = n + 1
    f = (f_min + f_max) / 2
    g_middle = 1 / kappa * Log(Re * (f / 2) ^ (1 / 2)) + b - (2 / f) ^ (1 / 2)
    g_lower = 1 / kappa * Log(Re * (f_min / 2) ^ (1 / 2)) + b - (2 / f_min) ^ (1 / 2)
    If (g_middle = 0 Or (f_max - f_min) / 2 < 1e-06) Then
      Exit Do
    Else
      If (g_middle * g_lower > 0) Then
        f_min = f
      Else
        f_max = f
      End If
    End If
    c_f = f
    If (n > 100) Then
      c_f = CVErr(xlErrNA)
      Exit Do
    End If
  Loop
End Function

' Useful implementation of Colebrook-White equation solver
Function Colebrook2(Rr As Double, Re As Double) As Double
  Dim f_min As Double, f_max As Double, f As Double
  Dim g_lower As Double, g_middle As Double
  Dim n As Integer

  f_min = (2.51 / Re) ^ 2 * (1 - Rr / 3.7) ^ (-2)
  f_max = ((2.51 / Re + Log(10) / 2) / (1 - Rr / 3.7)) ^ 2
  n = 0
  
  Do
    n = n + 1
    f = (f_min + f_max) / 2
    g_middle = -2 / Log(10) * Log(Rr / 3.7 + 2.51 / Re * f ^ (-1 / 2)) - f ^ (-1 / 2)
    g_lower = -2 / Log(10) * Log(Rr / 3.7 + 2.51 / Re * f_min ^ (-1 / 2)) - f_min ^ (-1 / 2)
    If (g_middle = 0 Or (f_max - f_min) / 2 < 1e-06) Then
      Exit Do
    Else
      If (g_middle * g_lower > 0) Then
        f_min = f
      Else
        f_max = f
      End If
    End If
    Colebrook2 = f
    If (n > 100) Then
      Colebrook2 = CVErr(xlErrNA)
      Exit Do
    End If
  Loop
End Function

Function Colebrook(Re As Double, a As Double, b As Double) As Double
  Dim aa As Double, bb As Double, c As Double, Fa As Double, Fb As Double, n As Integer
  aa = 1 / (Re ^ 2 * Exp(2 * b / a))
  bb = (a + Re) ^ 2 / (Re ^ 2 * (a + b) ^ 2)
  n = 0
  Do
    n = n + 1
    c = (aa + bb) / 2
    Fc = g_Colebrook(c, Re, a, b)
    Fa = g_Colebrook(aa, Re, a, b)
    If (Fc = 0 Or (bb - aa) / 2 < 1e-06) Then
      Exit Do
    Else
      If (Fc * Fa > 0) Then
        aa = c
      Else
        bb = c
      End If
    End If
    Colebrook = c
    If (n > 100) Then
      Colebrook = -2
      Exit Do
    End If
  Loop
End Function

Function g_Colebrook(f As Double, Re As Double, a As Double, b As Double)
  g_Colebrook = a * Log(Re * (f) ^ (1 / 2)) + b - (f) ^ (-1 / 2)
End Function

' Supporting function used for layered rotating cylinders
Function GeometricSeries(x As Double, i As Integer) As Double
  Dim ii As Integer
  GeometricSeries = 0
  For ii = 0 To i
    GeometricSeries = GeometricSeries + x ^ ii
  Next ii
End Function
