c
c     The program uses the theory developed in [Ramaty 1969 ApJ 158, 753;
c     Ramaty et al. 1994 ApJ 436, 941] to calculate gyrosynchrotron radiation 
c     from a power-law electron energy distribution:
c
c     u(E)=dn(E)/dE = A E^(-delta)  (MeV^-1)
c
c     A = 1/ XNORM normalizes the distribution to 1.
c
c     The program requires an input file, gyro.inp; the parameters in
c     this file define: 

c     delta        spectral index of electron distribution
c     NELECTRON    total number of electrons
c     bmag         magnetic field [gauss] (assumed uniform)
c     viewangle    viewing angle (angle between B and the line of sight (0<cs<1)
c                  cs can take on any positive value greater than 0 and less
c                  than 1; the appropriate formulae for cs=0 are given in Ramaty (1969);  
c                  these formulae have not yet been incorporated into the
c                  present routine; it appears that the routine works
c                  well for 0.1<cs<0.95.
c
c     asize        source size [arc sec]
c     height       source height [cm]
c     j1           index to define Emin
c     j2           index to define Emax
c                  define the range of electron energies used in the 
c                  integration, for example:
c
c                  j1=1 ; j2=120 corresponds to 0.01 - 10  MeV
c                  j1=29; j2=160 corresponds to 0.05 - 100 MeV
c                  j1=41; j2=160 corresponds to 0.10 - 100 MeV
c                  j1=41; j2=200 corresponds to 0.10 - 1000 MeV
c
c     etr          gyro/sync transition energy [MeV]
c                  below etr the full gyrosynchrotron formalism is used; above etr 
c                  the program uses the ultrarelativistic (Ginzburg and Syrovatskii) 
c                  formula; to calculate the total emissions it is sufficient
c                  to take etr about 3 MeV, except for cs close to 1 when etr should 
c                  be larger 
c 
c     np           plasma density
c
c     parameter kf (number of output frequencies) 
c    
c     e1d,e2d ord/xord mode emissivities in erg s^-1 sr^-1 Hz^-1 cm^-3
c     a1d,a2d ord/xord mode abs coefficients in cm^-1
c     phi1,phi1 ord/xord mode flux densities at Earth in SFU
c     rccd and rcd are degrees of polarization calculated 
c     from the emissivities and the flux densities, respectively;
c     All 8 quantities are arrays of size defined by kf.
c
c     The output is written into gyro-COEF.out, gyro-pol.out and gyro-flux.out
c============================================================
c
      Subroutine gyro(freq,kf,delta,nelectron,bmag,asize,flux)

      integer k,kf,j,j1,j2
c
      double precision delta,em,eu,el,de,XNORM
      double precision etr,gamma,gtr     
c      
      double precision alpha,bmag,vb,vp,ffp,np,vr
c    
      double precision g1em,g2em,g1ab,g2ab
      double precision an,an1,an2,ath1,ath2
c      
      double precision emfac,abfac  
      double precision PI,DTOR,AU,ARC2CM,M0,C,EC,E0,SFU 
c  
      double precision asize,height,radius,area
      double precision volume,density,omega
c      
      double precision viewangle,cs,ss
c
      double precision ffb,freq(kf)
c      
      double precision NELECTRON
c
      double precision e1,e2
      double precision a1,a2
      double precision arg1,arg2
      double precision e1d(kf),e2d(kf)
      double precision a1d(kf),a2d(kf)
      double precision phi1(kf),phi2(kf),phit(kf)
      double precision flux(kf) 
      double precision q(kf),v(kf),scd(kf)
      double precision rccd(kf),rcd(kf)            
c
      COMMON/input1/viewangle
      COMMON/input2/height
      COMMON/input3/j1
      COMMON/input4/j2
      COMMON/input5/etr
      COMMON/input6/np
c      
Cf2py INTENT(IN):: freq(kf)
Cf2py INTENT(IN):: kf
Cf2py INTENT(IN):: delta
Cf2py INTENT(IN):: nelectron
Cf2py INTENT(IN):: bmag
Cf2py INTENT(IN):: asize
Cf2py INTENT(OUT):: flux
Cf2py depend(freq,kf,delta,nelectron,bmag,asize) flux  
c
c------------------------------------------------------------
c 
c     Input parameters      
c
c------------------------------------------------------------
c
c      delta        ! spectral index of electron distribution
c      NELECTRON    ! total number of electrons
c      bmag         ! magnetic field [gauss]
c      viewangle    ! viewing angle
c      asize        ! source angular size [arc sec]
c      height       ! source height [cm]
c      j1           ! index to define Emin
c      j2           ! index to define Emax
c      etr          ! gyro/sync transition energy [MeV]
c      np           ! plasma density
c 
c------------------------------------------------------------
c
c     constants
c 
c------------------------------------------------------------
c
      PI  = 4.0d0*DATAN(1.0D0)
c
      DTOR   = PI/180.0d0                    ! degree --> rad
      AU     = 1.49597870d13                 ! astronomic Unit [cm]
      ARC2CM = (DTOR/3600.0d0)*AU            ! arcsec --> cm in Sun
      M0     = 9.1094d-28                    ! electron mass [g]
      C      = 2.998d10                      ! speed of light [cm/s]
      EC     = 4.803d-10                     ! electron charge [esu]
      E0     = (M0*C*C)/(1.6022d-12)/(1.0d6) ! electron rest energy [MeV]
      SFU    = 1.0d19                        ! erg/s/cm2/Hz --> s.f.u.
c 
c------------------------------------------------------------
c
c     parameters
c 
c------------------------------------------------------------
c
      cs    = dcos(viewangle*DTOR)         ! cos of viewing angle
c
c     verify viewing angle limits
c
         if (cs.lt.0.1d0.or.cs.gt.0.95d0) then
         write(*,*)'viewing angle beyond the limits'
         else
         continue
         endif
c   
      ss    = dsin(viewangle*DTOR)         ! sin of viewing angle
c
      vb    = 0.5d0/PI*(EC/M0/C)*bmag      ! gyrofrequency
      vp    = EC*dsqrt(np/PI/M0)           ! plasma frequency
      ffp   = vp/vb                        ! ratio plasma/gyro frequency
      alpha = (3.0d0/2.0d0)/ffp            ! Razin parameter
      vr    = (2.0d0/3.0d0)*(vp*vp)/vb/ss  ! Razin effect cutoff frequency
c
      emfac = (EC*EC*EC)/(M0*C*C)          ! emissivity scale factor
      abfac = 4.0d0*(PI*PI)*EC             ! absorption scale factor
c
      radius  = asize*ARC2CM/2.0d0         ! source radius [cm]     
c
      area    = PI*radius*radius           ! source area [cm^2]     
      omega   = area/(AU*AU)               ! solid angle [sr]
      volume  = area*height                ! source volume [cm^3]
c  
c------------------------------------------------------------
c
c     calculate factor XNORM to normalize the electron energy distribution to 1
c 
c------------------------------------------------------------
c
      XNORM=0.0d0
c
      do j=j1,j2
      el=10.0d0**(0.025d0*(j-1)-2.0d0)
      eu=10.0d0**(0.025d0*j-2.0d0)
      em=10.0d0**(0.025d0*(j-0.5d0)-2.0d0)
c
      de=eu-el
c
      XNORM=XNORM+em**(-delta)*de
      enddo     
c
c------------------------------------------------------------
c
c     calculate density
c 
c------------------------------------------------------------
c
      density = NELECTRON/volume        ! source density [electrons/cm^3]
c
c------------------------------------------------------------
c
c     start loop on frequency
c 
c------------------------------------------------------------
c
      do k=1,kf
c      
      ffb=freq(k)/vb
c 
c------------------------------------------------------------
c
c     calculate refraction index
c 
c------------------------------------------------------------
c       
      call refr(ffb,ffp,cs,an1,an2,ath1,ath2)
c 
c------------------------------------------------------------
c
c     start integration over energy
c 
c------------------------------------------------------------
c
      e1=0.0d0
      e2=0.0d0
      a1=0.0d0
      a2=0.0d0
c 
      do j=j1,j2
      el=10.0d0**(0.025d0*(j-1)-2.0d0)
      eu=10.0d0**(0.025d0*j-2.0d0)
      em=10.0d0**(0.025d0*(j-0.5d0)-2.0d0)
c
      de=eu-el
c
      gamma=em/E0+1.0d0
      gtr=etr/E0+1.0d0      
c
      g1em=0.0d0
      g2em=0.0d0
      g1ab=0.0d0
      g2ab=0.0d0   
c      
c------------------------------------------------------------
c
c     E < Etr
c 
c------------------------------------------------------------
c 
      if(gamma.lt.gtr)then
c
c     ordinary mode
c
        if(ffb.gt.ffp)then
        an=dsqrt(an1)
        call gsy(gamma,delta,ffb,cs,g1em,g1ab,an,ath1)
c
        else
c
        g1em=0.0d0
        g1ab=0.0d0    
c         
        endif
c
c     extraordinary mode
c
        if(ffb.gt.(dsqrt(ffp**2.0d0+0.25d0)+0.5d0))then
        an=dsqrt(an2)
        call gsy(gamma,delta,ffb,cs,g2em,g2ab,an,ath2)
c  
        else
c
        g2em=0.0d0
        g2ab=0.0d0    
c         
        endif
c      
c------------------------------------------------------------
c
c     E > Etr
c 
c------------------------------------------------------------
c        
      else if(gamma.ge.gtr)then
c
c     ordinary and extraordinary modes
c       
      if(ffb.gt.(dsqrt(ffp**2.0d0+0.25d0)+0.5d0))then
c
      call ssy(gamma,delta,ffb,cs,g1em,g2em,g1ab,g2ab,alpha)
c
        else
c
        g1em=0.0d0
        g1ab=0.0d0 
        g2em=0.0d0
        g2ab=0.0d0    
c         
      endif
c
      endif 
c     
c------------------------------------------------------------
c
      e1=e1+g1em*em**(-delta)*de*bmag*emfac
c
      e2=e2+g2em*em**(-delta)*de*bmag*emfac
c
      a1=a1+g1ab*em**(-delta)*de/bmag*abfac
c
      a2=a2+g2ab*em**(-delta)*de/bmag*abfac
c      
      enddo
c 
c------------------------------------------------------------
c
c     end of integration over energy
c 
c------------------------------------------------------------
c
c     emissivities and absorption coefficients
c 
c------------------------------------------------------------
c
      e1d(k)=(NELECTRON/XNORM)*e1/volume
      e2d(k)=(NELECTRON/XNORM)*e2/volume
      a1d(k)=(NELECTRON/XNORM)*a1/volume
      a2d(k)=(NELECTRON/XNORM)*a2/volume
c 
c------------------------------------------------------------
c
c     calculate polarization
c 
c------------------------------------------------------------
c      
      if(e2d(k).gt.0.0d0)then
        rccd(k)=(e2d(k)-e1d(k))/(e2d(k)+e1d(k))
      else
        rccd(k)=0.0d0
      endif
c 
c------------------------------------------------------------
c
c     calculate flux
c 
c------------------------------------------------------------
c
      arg1=a1d(k)*height
c      
      if(arg1.lt.0.001d0)then
c      
        phi1(k)=e1d(k)*volume/AU/AU      
c        
      else
c      
        phi1(k)=omega*(e1d(k)/a1d(k))*(1.0d0-dexp(-arg1))
c     
      endif                          
c
      arg2=a2d(k)*height
c      
      if(arg2.lt.0.001d0)then
c      
        phi2(k)=e2d(k)*volume/AU/AU
c        
      else
c      
        phi2(k)=omega*(e2d(k)/a2d(k))*(1.0d0-dexp(-arg2))
c     
      endif                                
c 
c------------------------------------------------------------
c
c     calculate Stokes parameters
c 
c------------------------------------------------------------
c
c     total flux
c 
c------------------------------------------------------------
c
      phit(k)=phi1(k)+phi2(k)
c 
c------------------------------------------------------------
c
c     convert fluxes from erg cm^-2 s^-1 Hz^-1 to W m^-2 s^-1 Hz^-1 and to SFU
c 
c------------------------------------------------------------
c
      if(freq(k).ge.vb)then   
      flux(k) = phit(k)*SFU
      else
      continue
      endif        
c 
c------------------------------------------------------------
c
c     polarization
c 
c------------------------------------------------------------
c      
      q(k)=phi1(k)*(1.0d0-ath1**2.0d0)/(1.0d0+ath1**2.0d0)
     &    +phi2(k)*(1.0d0-ath2**2.0d0)/(1.0d0+ath2**2.0d0)
c
      v(k)=2.0d0*(phi1(k)*ath1/(1.0d0+ath1**2.0d0)
     &           +phi2(k)*ath2/(1.0d0+ath2**2.0d0))
c     
      if(phit(k).gt.0.0d0)then
        rcd(k)=(phi2(k)-phi1(k))/phit(k)
        scd(k)=v(k)/abs(v(k))
     &        *dsqrt(q(k)**2.0d0+v(k)**2.0d0)/phit(k)
      else
        rcd(k)=0.0d0
        scd(k)=0.0d0
      endif
c
      enddo
c 
c------------------------------------------------------------
c      
c     end of loop over frequency
c 
c------------------------------------------------------------
c
c
      return
      end
c 
c------------------------------------------------------------
c
c     end of subroutine
c 
c------------------------------------------------------------
c      
c--------synchrotron routine---------------------------------
c 
c------------------------------------------------------------
c
      subroutine ssy(gamma,delta,ffb,cs,g1em,g2em,g1ab,g2ab,alpha)
c      
      IMPLICIT DOUBLE PRECISION(A-H,O-Z)
c
      dimension xd(34),fd(34)
      data xd/0.001d0,0.005d0,0.01d0,0.025d0,0.05d0,0.075d0,0.1d0,
     &        0.15d0,0.2d0,0.25d0,0.3d0,0.4d0,0.5d0,0.6d0,0.7d0,0.8d0,
     &        0.9d0,1.d0,1.2d0,1.4d0,1.6d0,1.8d0,2.d0,2.5d0,
     &        3.d0,3.5d0,4.d0,4.5d0,5.d0,6.d0,7.d0,8.d0,9.d0,10.d0/
      data fd/0.213d0,0.358d0,0.445d0,0.583d0,0.702d0,0.722d0,0.818d0,
     &        0.874d0,0.904d0,0.917d0,0.919d0,0.901d0,0.872d0,
     &        0.832d0,0.788d0,0.742d0,0.694d0,0.655d0,
     &        0.566d0,0.486d0,0.414d0,0.354d0,0.301d0,0.2d0,0.13d0,
     &        0.0845d0,0.0541d0,0.0339d0,0.0214d0,0.0085d0,
     &        0.0033d0,0.0013d0,0.0005d0,0.00019d0/
c
      PI  = 4.0d0*DATAN(1.0D0)
c
      ss=dsqrt(1.0d0-cs*cs)
c            
      ffc=ffb*2.0d0/3.0d0/ss/gamma/gamma*
     &(1.0d0+9.0d0/4.0d0*(gamma*gamma-1.0d0)/alpha/alpha/ffb/ffb)**1.5d0
C   
      X=ffc 
C
C *****************************************************************
C
C     calculation of function F = X*Int_X^inf K(5/3,Y) dY 
C 
C******************************************************************
C      
      IF(X.LE.1.0d-3)THEN
C
        F=4.0d0*PI/dsqrt(3.0d0)/2.67894d0*(X/2.0d0)**0.333333d0
     $   *(1.0d0-2.67894d0/2.0d0*(X/2.0d0)**0.66666d0)    
C
        ELSE IF(X.GT.10.0d0)THEN
C
        F=dsqrt(PI*X/2.0d0)*dexp(-X)*(1.0d0+55.0d0/72.0d0/X)
C
      ELSE
C        
C------------------------------------------------------------
C
C     Ramaty's approximate calculation
C      
C------------------------------------------------------------
C      
      call sear(xd,fd,ffc,F)     
C
      ENDIF
C           
C******************************************************************
C
      gtot=(dsqrt(3.0d0)/4.0d0/PI)*ss*F
     & /dsqrt(1.0d0+9.0d0/4.0d0*(gamma*gamma-1.0d0)/alpha/alpha/ffb/ffb)
c
      g1em=gtot/2.0d0      
c      
      g2em=gtot/2.0d0      
c      
      g1ab=g1em/ffb/ffb
     &    *(delta*gamma*(gamma+1.0d0)+2.0d0*gamma*gamma-1.0d0)
     &    /gamma/(gamma**2.0d0-1.0d0)
c     
      g2ab=g2em/ffb/ffb
     &    *(delta*gamma*(gamma+1.0d0)+2.0d0*gamma*gamma-1.0d0)
     &    /gamma/(gamma**2.0d0-1.0d0)  
c  
      return
      end
c 
c------------------------------------------------------------
c      
c-----------search routine-----------------------------------
c 
c------------------------------------------------------------
c
      SUBROUTINE SEAR(XC,SGC,X,S)
c
      IMPLICIT DOUBLE PRECISION(A-H,O-Z)
c      
      dimension XC(34),SGC(34)
      I=1
   12 IF(XC(I).GE.X)GO TO  13
      I=I+1
      GO TO 12
   13 S=(SGC(I)*(X-XC(I-1))+SGC(I-1)*(XC(I)-X ))/(XC(I)-XC(I-1))
      RETURN
      END
c 
c------------------------------------------------------------
c      
c------------gyrosynchrotron routine-------------------------
c 
c------------------------------------------------------------
c
      subroutine gsy(gamma,delta,ffb,cs,g12em,g12ab,an,ath)
c
      IMPLICIT DOUBLE PRECISION(A-H,O-Z)
      external bes
      external bespr      
c
      PI  = 4.0d0*DATAN(1.0D0)
c
      beta=dsqrt(gamma*gamma-1.0d0)/gamma
      ss=dsqrt(1.0d0-cs*cs)
      ffc=ffb*2.0d0/3.0d0/ss/gamma/gamma
      if(ffc.ge.20.0d0)then
      g12em=0.0d0
      g12ab=0.0d0      
      return
      else
      is1=int(ffb*gamma*(1.0d0-an*beta*cs)+1.0d0)
      is2=int(ffb*gamma*(1.0d0+an*beta*cs))
      sum12em=0.0d0
      sum12ab=0.0d0      
      do i=is1,is2
      cphis=(1.0d0-i/ffb/gamma)/beta/cs/an
      sphis=dsqrt(1.0d0-cphis*cphis)
      xs=i*an*beta*ss*sphis/(1.0d0-an*beta*cs*cphis)
      if(ffb.gt.50.0d0)then
      xstr=0.8d0
      if(gamma.gt.5.0d0)xstr=0.9d0
      if(gamma.gt.10.0d0)xstr=0.95d0
      if(gamma.gt.15.0d0)xstr=0.96d0
      if(xs.lt.xstr*i)goto 10
      endif
      if(ffb.gt.250.0d0)then
      xstr=0.9d0
      if(gamma.gt.5.0d0)xstr=0.92d0
      if(gamma.gt.10.0d0)xstr=0.97d0
      if(gamma.gt.15.0d0)xstr=0.98d0
      if(xs.lt.xstr*i)goto 10
      endif
      
      b=0.0d0
      call bes(i,xs,b)
      call bespr(i,xs,bpr)
c
      f12=(-beta*sphis*bpr+ath*(cs/ss/an-beta*cphis/ss)*b)**2.d0
c     
      h2=(delta*gamma*(gamma+1.0d0)+2.0d0*gamma*gamma-1.0d0)
     &  /gamma/(gamma*gamma-1.0d0)        
c    
      f12em=f12
      f12ab=f12*h2
      
c      
      s12oldem=sum12em
      sum12em=sum12em+f12em
c 
      s12oldab=sum12ab
      sum12ab=sum12ab+f12ab
c     
      if(s12oldem.gt.0.0d0.and.s12oldab.gt.0.0d0)then
      if((sum12em-s12oldem)/s12oldem.lt.1.0d-12.and.
     &   (sum12ab-s12oldab)/s12oldab.lt.1.0d-12)goto 11
      endif
10    continue
      enddo
11    continue
      g12em=sum12em/beta/2.0d0/cs*ffb/(1.0d0+ath**2.0d0)
      g12ab=sum12ab/beta/2.0d0/cs/ffb/(1.0d0+ath**2.0d0)/an
      return
      endif
      end
c 
c------------------------------------------------------------
c      
c-----index of refraction and polarization coefficient-------
c 
c------------------------------------------------------------
c
      subroutine refr(ffb,ffp,cs,an1,an2,ath1,ath2)
c
      IMPLICIT DOUBLE PRECISION(A-H,O-Z)      
c
      ss=dsqrt(1.0d0-cs*cs)
      anum=2.0d0*ffp*ffp*(ffp*ffp-ffb*ffb)
      dnum1=+dsqrt(ffb**4.0d0*ss**4.0d0+4.0d0*ffb**2.0d0
     &      *(ffp**2.0d0-ffb**2.0d0)**2.0d0*cs**2.0d0)-
     &     2.0d0*ffb**2.0d0*(ffp**2.0d0-ffb**2.0d0)-ffb**2.0d0*ss**2.0d0
      dnum2=-dsqrt(ffb**4*ss**4.0d0+4.0d0*ffb**2
     &     *(ffp**2.0d0-ffb**2.0d0)**2.0d0*cs**2.0d0)-
     &     2.0d0*ffb**2.0d0*(ffp**2.0d0-ffb**2.0d0)-ffb**2*ss**2.0d0
      an1=1.0d0+anum/dnum1
      an2=1.0d0+anum/dnum2
      aknum=2.0d0*ffb*(ffp*ffp-ffb*ffb)*cs
      dknum1=+dsqrt(ffb**4.0d0*ss**4.0d0+4.0d0*ffb**2.0d0
     &      *(ffp**2.0d0-ffb**2.0d0)**2.0d0*cs**2.0d0)-
     &      ffb**2.0d0*ss**2.0d0
      dknum2=-dsqrt(ffb**4.0d0*ss**4.0d0+4.0d0*ffb**2.0d0
     &      *(ffp**2.0d0-ffb**2.0d0)**2.0d0*cs**2.0d0)-
     &      ffb**2.0d0*ss**2.0d0
      ath1=-aknum/dknum1
      ath2=-aknum/dknum2
c
      return
      end
c 
c------------------------------------------------------------
c      
c--------------Bessel Function routines----------------------
c 
c------------------------------------------------------------
c
      subroutine bespr(n,x,bpr)     
c
      IMPLICIT DOUBLE PRECISION(A-H,O-Z)
      
c
      b=0.0d0
      b1=0.0d0
      n1=n+1
      call bes(n1,x,b1)
      call bes(n,x,b)
      bpr=-b1+n/x*b
      return
      end
      
      subroutine bes(n,x,b)
c
      IMPLICIT DOUBLE PRECISION(A-H,O-Z)
c
      if(n.eq.0)b=bessj0(x)
      if(n.eq.1)b=bessj1(x)
      if(n.ge.2)then
        b=bessj(n,x)
      endif
      return
      end
c
      FUNCTION BESSJ0(X)
c      
      IMPLICIT DOUBLE PRECISION(A-H,O-Z)
c
      DATA P1,P2,P3,P4,P5/1.D0,-.1098628627D-2,.2734510407D-4,
     *    -.2073370639D-5,.2093887211D-6/, Q1,Q2,Q3,Q4,Q5/-.1562499995D-
     *1,
     *    .1430488765D-3,-.6911147651D-5,.7621095161D-6,-.934945152D-7/
      DATA R1,R2,R3,R4,R5,R6/57568490574.D0,-13362590354.D0,651619640.7D
     *0,
     *    -11214424.18D0,77392.33017D0,-184.9052456D0/,
     *    S1,S2,S3,S4,S5,S6/57568490411.D0,1029532985.D0,
     *    9494680.718D0,59272.64853D0,267.8532712D0,1.D0/
      IF(DABS(X).LT.8.0d0)THEN
        Y=X**2
        BESSJ0=(R1+Y*(R2+Y*(R3+Y*(R4+Y*(R5+Y*R6)))))
     *      /(S1+Y*(S2+Y*(S3+Y*(S4+Y*(S5+Y*S6)))))
      ELSE
        AX=DABS(X)
        Z=8.0d0/AX
        Y=Z**2.0d0
        XX=AX-.785398164d0
        BESSJ0=DSQRT(.636619772d0/AX)*(DCOS(XX)*(P1+Y*(P2+Y*(P3+Y*(P4+Y
     *      *P5))))-Z*DSIN(XX)*(Q1+Y*(Q2+Y*(Q3+Y*(Q4+Y*Q5)))))
      ENDIF
      RETURN
      END
      
      FUNCTION BESSJ1(X)
c
      IMPLICIT DOUBLE PRECISION(A-H,O-Z)
c
      DATA R1,R2,R3,R4,R5,R6/72362614232.D0,-7895059235.D0,242396853.1D0
     *,
     *    -2972611.439D0,15704.48260D0,-30.16036606D0/,
     *    S1,S2,S3,S4,S5,S6/144725228442.D0,2300535178.D0,
     *    18583304.74D0,99447.43394D0,376.9991397D0,1.D0/
      DATA P1,P2,P3,P4,P5/1.D0,.183105D-2,-.3516396496D-4,.2457520174D-5
     *,
     *    -.240337019D-6/, Q1,Q2,Q3,Q4,Q5/.04687499995D0,-.2002690873D-3
     *,
     *    .8449199096D-5,-.88228987D-6,.105787412D-6/
      IF(DABS(X).LT.8.0d0)THEN
        Y=X**2.0d0
        BESSJ1=X*(R1+Y*(R2+Y*(R3+Y*(R4+Y*(R5+Y*R6)))))
     *      /(S1+Y*(S2+Y*(S3+Y*(S4+Y*(S5+Y*S6)))))
      ELSE
        AX=DABS(X)
        Z=8.0d0/AX
        Y=Z**2.0d0
        XX=AX-2.356194491d0
        BESSJ1=DSQRT(.636619772d0/AX)*(DCOS(XX)*(P1+Y*(P2+Y*(P3+Y*(P4+Y
     *      *P5))))-Z*DSIN(XX)*(Q1+Y*(Q2+Y*(Q3+Y*(Q4+Y*Q5)))))
     *      *SIGN(1.0d0,X)
      ENDIF
      RETURN
      END
      
      FUNCTION BESSJ(N,X)
c      
      IMPLICIT DOUBLE PRECISION(A-H,O-Z)
c
      PARAMETER (IACC=40,BIGNO=1.E10,BIGNI=1.E-10)
C      IF(N.LT.2)PAUSE 'bad argument N in BESSJ'
      TOX=2.0d0/X
      IF(X.GT.FLOAT(N))THEN
        BJM=BESSJ0(X)
        BJ=BESSJ1(X)
        DO 11 J=1,N-1
          BJP=J*TOX*BJ-BJM
          BJM=BJ
          BJ=BJP
11      CONTINUE
        BESSJ=BJ
      ELSE
        M=2*((N+INT(SQRT(FLOAT(IACC*N))))/2)
        BESSJ=0.0d0
        JSUM=0
        SUM=0.0d0
        BJP=0.0d0
        BJ=1.0d0
        DO 12 J=M,1,-1
          BJM=J*TOX*BJ-BJP
          BJP=BJ
          BJ=BJM
          IF(DABS(BJ).GT.BIGNO)THEN
            BJ=BJ*BIGNI
            BJP=BJP*BIGNI
            BESSJ=BESSJ*BIGNI
            SUM=SUM*BIGNI
          ENDIF
          IF(JSUM.NE.0)SUM=SUM+BJ
          JSUM=1-JSUM
          IF(J.EQ.N)BESSJ=BJP
12      CONTINUE
        SUM=2.0d0*SUM-BJ
        BESSJ=BESSJ/SUM
      ENDIF
      RETURN
      END

