' Functions of constants
Function Gval() As Double
  Gval = 6.67384e-11
End Function
Function Pi() As Double
  Pi = 3.14159265358979
End Function
Function AU() As Double
  AU = 149597871000#
End Function
Function Skylab() As Double
  Skylab = 34400
End Function
Function atm() As Double
  atm = 101325
End Function
Function sun_mass() As Double
  sun_mass = 1.989e+30
End Function
Function Stefan_const() As Double
  Stefan_const = 5.6704e-08
End Function
' Density approximation function
Function density_type3(T1 As String, T2 As String) As Double
  density_type3 = density_kra(T1)
  If (density_type3 = 1300) Then
    density_type3 = density_kra(T2)
  End If
End Function
Function density_type2(T1 As String, T2 As String) As Double
  density_type2 = density_type(T1)
  If (density_type2 = 1300) Then
    density_type2 = density_type(T2)
  End If
End Function
Function density_kra(Tp As String) As Double
  Dim c_array() As Variant, s_array() As Variant, m_array As String, n As Integer, T As String
  T = LCase(Left(Tp, 1))
  c_array = Array("C", "D", "P", "T", "B", "G", "F")
  s_array = Array("S", "K", "Q", "V", "R", "A", "E")
  density_kra = 1300
  m_array = "M"
  For n = 0 To 6
    If (T = LCase(c_array(n))) Then
      density_kra = 1380
    End If
    If (T = LCase(s_array(n))) Then
      density_kra = 2710
    End If
  Next n
  If (T = LCase(m_array)) Then
    density_kra = 5320
  End If
End Function

Function density_type(Tp As String) As Double
  Dim T_first As String
  T_first = LCase(Left(Tp, 1))
  density_type = -2
  If (T_first = "c") Then
    density_type = 1166.76
  ElseIf (T_first = "s") Then
    density_type = 1985.445
  ElseIf (T_first = "m") Then
    density_type = 2766.776
  ElseIf (T_first = "v") Then
    density_type = 1456.6
  Else
    density_type = 1300
  End If
End Function
' Function to find the radius of maximum N2 mass
Function R_N2max(M As Double, rho As Double) As Double
  Dim n As Integer, delta As Double, dPdR2 As Double, dPdRp As Double
  n = 1
  If (P_RM(0, M, rho) < 0.21 * atm()) Then
    R_N2max = -3
  Else
    
'    R_N2max = R_MP(M, 0.21 * atm(), rho) ' first attempt
    dPdRp = dPdR_RM(0, M, rho)
    dPdR2 = (dPdR_RM(0.01, M, rho) - dPdRp) / 0.01
    R_N2max = Math.Sqr((0.21 * atm() - P_RM(0, M, rho)) * 3 / dPdR2)
    Do
      dPdRp = dPdR_RM(R_N2max, M, rho)
      dPdR2 = (dPdR_RM(R_N2max + 0.01, M, rho) - dPdRp) / 0.01
      delta = -(P_RM(R_N2max, M, rho) - 0.21 * atm() + R_N2max * dPdRp / 3) / (4 * dPdRp / 3 + R_N2max * dPdR2 / 3)
      R_N2max = R_N2max + delta
      n = n + 1
      If (Math.Abs(delta / R_N2max) < 1e-07) Then
        Exit Do
      ElseIf (n > 20) Then
        R_N2max = -2
        Exit Do
      End If
    Loop
  End If
End Function
' Functions for solar system transfer orbits
Function inclined_hoh_avg(a As Double, i As Double) As Double
  inclined_hoh_avg = 0.5 * (inclined_hoh(a, i) + inclined_hoh_min(a, i))
End Function
Function inclined_hoh(a As Double, i As Double)
  Dim ve As Double, v1 As Double, v2 As Double, gv As Double, v1p
  v1 = hohmann1_mrr(sun_mass(), AU(), a * AU())
  ve = Math.Sqr(Gval() * sun_mass() / AU())
  gv = ve + v1
  v1p = Math.Sqr(ve ^ 2 + gv ^ 2 - 2 * gv * ve * Math.Cos(i * Pi() / 180#))
  v2 = hohmann2_mrr(sun_mass(), AU(), a * AU())
  inclined_hoh = v1p + v2
End Function
Function inclined_hoh_min(a As Double, i As Double)
  Dim ve As Double, v1 As Double, v2 As Double, gv As Double, v2p
  v1 = hohmann1_mrr(sun_mass(), AU(), a * AU())
  v2 = hohmann2_mrr(sun_mass(), AU(), a * AU())
  ve = Math.Sqr(Gval() * sun_mass() / (a * AU()))
  gv = ve - v2
  v2p = Math.Sqr(ve ^ 2 + gv ^ 2 - 2 * gv * ve * Math.Cos(i * Pi() / 180#))
  inclined_hoh_min = v1 + v2p
End Function
Function hohmann1_mrr(M As Double, r1 As Double, r2 As Double) As Double
  If (r2 > r1) Then
    hohmann1_mrr = (Gval() * M / r1) ^ (1 / 2) * ((2 * r2 / (r1 + r2)) ^ (1 / 2) - 1)
  Else
    hohmann1_mrr = (Gval() * M / r1) ^ (1 / 2) * (1 - (2 * r2 / (r2 + r1)) ^ (1 / 2))
  End If
End Function
Function hohmann2_mrr(M As Double, r1 As Double, r2 As Double) As Double
  If (r2 > r1) Then
    hohmann2_mrr = (Gval() * M / r2) ^ (1 / 2) * (1 - (2 * r1 / (r1 + r2)) ^ (1 / 2))
  Else
    hohmann2_mrr = (Gval() * M / r2) ^ (1 / 2) * ((2 * r1 / (r2 + r1)) ^ (1 / 2) - 1)
  End If
End Function
' Function returns the tether mass to payload mass ratio for rotating tether in space
Function tether_rot(v As Double, ss As Double) As Double
  Dim alpha As Double
  tether_rot = 2#
  alpha = v / Math.Sqr(2 * ss)
  tether_rot = Pi() * alpha * Application.WorksheetFunction.Erf(alpha) * Math.Exp(alpha ^ 2)
End Function
' --- functions related to asteroid abundance ----
Function dNdD_wiki(D As Double)
  dNdD_wiki = 3762457.114 * D ^ (-3.12063)  ' asteroid size distribution from Wikipedia interpolation
End Function
Function dNdD_JPL(D As Double)
  ' asteroid size distribution using JPL search limited to certain range: about 131 km to 200
  dNdD_JPL = 762000000# * D ^ (-3.6)
End Function
Function dNdD_MB(D As Double)
  ' asteroid size distribution using fitted function to main belt
  ' distribution published in literature
  dNdD_MB = 6154110.296 * D ^ (-3.183317186)
End Function
' Functions related to the absolute magnitude
Function dia_p(H As Double, P As Double) As Double
  dia_p = 1329# * 10 ^ (-0.2 * H) / (P) ^ (0.5)
End Function
Function dia(H As Double) As Double
  dia = 1329# * 10 ^ (-0.2 * H) / (0.2) ^ (0.5)
End Function
Function H_dia(dia As Double) As Double
  H_dia = -Log(dia * Math.Sqr(0.2) / 1329) / (0.2 * Log(10#))
End Function
Function mass(H As Double) As Double
  mass = 1329# * 10 ^ (-0.2 * H) / (0.2) ^ (0.5)
End Function

' Gravity balloon functions
Function P_M(M As Double, rho As Double)
  P_M = P_RM(0#, M, rho)
End Function
Function M_P_small(P As Double, rho As Double) As Double
  M_P_small = (P * (rho * 4 / 3 * Pi()) ^ (2 / 3) / (2 / 3 * Gval() * rho ^ 2 * Pi())) ^ (3 / 2)
End Function
'----based on second revision of mathematics ---
' Functions based on (M,R,t) tripple
Function M_Rt(R As Double, T As Double, rho As Double) As Double
  M_Rt = (4# / 3#) * Pi() * rho * ((R + T) ^ 3 - R ^ 3)
End Function
Function R_Mt(M As Double, T As Double, rho As Double) As Double
  R_Mt = (-T + (T ^ 2 - 4 * ((T ^ 2) / 3 - M / (4 * Pi() * rho * T))) ^ (1 / 2)) / (2)
End Function
Function t_RM(R As Double, M As Double, rho As Double) As Double
  t_RM = (M / ((4 / 3) * Pi() * rho) + R ^ 3) ^ (1 / 3) - R
End Function
Function dtdR_RM(R As Double, M As Double, rho As Double) As Double
  dtdR_RM = R ^ 2 / (3 * M / (4 * Pi() * rho) + R ^ 3) ^ (2 / 3) - 1
End Function
' Composite function
Function dPdR_RM(R As Double, M As Double, rho As Double) As Double
  dPdR_RM = dPdR_Rt(R, t_RM(R, M, rho), rho) + dPdt_Rt(R, t_RM(R, M, rho), rho) * dtdR_RM(R, M, rho)
End Function
' Functions based on (P,R,t) tripple
Function P_Rt(R As Double, T As Double, rho As Double) As Double
  P_Rt = (2# / 3) * Pi() * Gval() * (T * rho) ^ 2 * (3 * R + T) / (R + T)
End Function
Function dPdt_Rt(R As Double, T As Double, rho As Double) As Double
  dPdt_Rt = (4# / 3) * rho ^ 2 * Pi() * Gval() * T * (3 * R ^ 2 + 3 * R * T + T ^ 2) / (R + T) ^ 2
End Function
Function dPdR_Rt(R As Double, T As Double, rho As Double) As Double
  dPdR_Rt = 4 * T ^ 3 * Gval() * Pi() * rho ^ 2 / (3 * (R + T) ^ 2)
End Function
Function R_Pt(P As Double, T As Double, rho As Double) As Double
  R_Pt = (1# / 3) * T * (3 * P - 2 * rho ^ 2 * Pi() * Gval() * T ^ 2) / (-P + 2 * rho ^ 2 * Pi() * Gval() * T ^ 2)
End Function
Function t_RP(R As Double, P As Double, rho As Double) As Double
  Dim n As Integer, delta As Double
  t_RP = 1.366 * (P / (2 * Gval() * Pi())) ^ (1# / 2) / rho
  n = 1
  Do
    delta = -(P_Rt(R, t_RP, rho) - P) / dPdt_Rt(R, t_RP, rho)
    t_RP = t_RP + delta
    n = n + 1
    If (Math.Abs(delta / t_RP) < 1e-06) Then
      Exit Do
    ElseIf (n > 20) Then
      t_RP = -2
      Exit Do
    End If
  Loop
End Function
' Functions based on the (P,R,M) tripple
Function M_RP(R As Double, P As Double, rho As Double) As Double
  M_RP = M_Rt(R, t_RP(R, P, rho), rho)
End Function
Function P_RM(R As Double, M As Double, rho As Double) As Double
  P_RM = P_Rt(R, t_RM(R, M, rho), rho)
End Function
Function R_MP(M As Double, P As Double, rho As Double) As Double
  Dim n As Integer, delta As Double
  R_MP = R_Mt(M, (P / (2 * Pi() * Gval())) ^ (1 / 2) / rho, rho) - 0.5 * (P / (2 * Pi() * Gval())) ^ (1 / 2) / rho
  n = 1
  Do
    delta = -(P_RM(R_MP, M, rho) - P) / dPdR_RM(R_MP, M, rho)
    R_MP = R_MP + delta
    n = n + 1
    If (Math.Abs(delta * rho / (P / (2 * Gval() * Pi()))) ^ (1 / 2) < 1e-06) Then    ' divide by est. value of t
      Exit Do
    ElseIf (n > 20) Then
      R_MP = -2
      Exit Do
    End If
  Loop
End Function
' root_abc used for a calculation related to tidal forces
Function root_abc(a As Double, b As Double, c As Double) As Double
  Dim n As Integer, delta As Double
  root_abc = (b / a) ^ (1 / 4)
  n = 1
  Do
    delta = -(a * root_abc ^ 4 - b + c * root_abc ^ 3) / (4 * a * root_abc ^ 3 + 3 * c * root_abc ^ 2)
    root_abc = root_abc + delta
    n = n + 1
    If (Math.Abs(delta / root_abc) < 1e-06) Then
      Exit Do
    ElseIf (n > 20) Then
      root_abc = -2
      Exit Do
    End If
  Loop
End Function
' Functions based on (P,S,R or t) tripple
Function P_RS(R As Double, S As Double, rho As Double) As Double
  P_RS = (2# / 3) * Pi() * Gval() * rho ^ 2 * (S - R) ^ 2 * (S + 2 * R) / S
End Function
Function dPdR_RS(R As Double, S As Double, rho As Double) As Double
  dPdR_RS = 4 * Pi() * Gval() * rho ^ 2 * R * (R - S) / S
End Function
Function R_PS(P As Double, S As Double, rho As Double) As Double
  Dim n As Integer, delta As Double
  R_PS = 0.9 * S
  n = 1
  Do
    delta = -(P_RS(R_PS, S, rho) - P) / dPdR_RS(R_PS, S, rho)
    R_PS = R_PS + delta
    n = n + 1
    If (Math.Abs(delta / S) < 1e-06) Then
      Exit Do
    ElseIf (n > 20) Then
      R_PS = -2
      Exit Do
    End If
  Loop
End Function
