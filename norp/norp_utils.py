import astropy.io.fits as iofits
from datetime import datetime, timezone
posicao = []


def onclick(event):

    print(event)
    # Anexa os dados do clique na list posição.
    posicao.append([event.xdata, event.ydata])
    # Imprime uma linha no local clicado.
    plt.plot([posicao[-1][0], posicao[-1][0]], [-20, 100])

#---norp_rd_obsDay
#   Function for obtaining the observing day [JST]
#   Output: string
def norp_rd_obsDay(filename):
    hdulist = iofits.open(filename)
    obsDay = hdulist[0].header['DATE-OBS']
    hdulist.close()
    return obsDay

#---norp_rd_sttim
#   Function for obtaining the start time of the observation [UT]
#   Output: string
def norp_rd_sttim(filename):
    hdulist = iofits.open(filename)
    stTim = hdulist[0].header['DATE-BEG']
    hdulist.close()
    return stTim

#---norp_rd_edtim
#   Function for obtaining the end time of the observation [UT]
#   Output: string
def norp_rd_edtim(filename):
    hdulist = iofits.open(filename)
    edTim = hdulist[0].header['DATE-END']
    hdulist.close()
    return edTim

#---norp_rd_existFreq
#   Function for showing the existed observing frequencies in the file
#   Output: Dictinoary
def norp_rd_existFreq(filename):
    exFreq = {'1GHz':0, '2GHz':0, '3.75GHz':0, '9.4GHz':0, '17GHz':0, '35GHz':0, '80GHz':0}
    hdulist = iofits.open(filename)
    pheader = hdulist[0].header
    keys =[]
    for name in pheader.keys():
        keys.append(name)
    hdulist.close()
    if keys.count('FREQ1') == 1 :
        exFreq['1GHz'] = 1
    if keys.count('FREQ2') == 1 :
        exFreq['2GHz'] = 1
    if keys.count('FREQ3') == 1 :
        exFreq['3.75GHz'] = 1
    if keys.count('FREQ4') == 1 :
        exFreq['9.4GHz'] = 1
    if keys.count('FREQ5') == 1 :
        exFreq['17GHz'] = 1
    if keys.count('FREQ6') == 1 :
        exFreq['35GHz'] = 1
    if keys.count('FREQ7') == 1 :
        exFreq['80GHz'] = 1
    return exFreq

#---norp_rd_dailyFlux
#   Function for getting the daily fluxes, which are calculated manualy, from PHU
#   Output: Dictinoary
def norp_rd_dailyFlux(filename):
    dailyFlux= {'1GHz':-1000, '2GHz':-1000, '3.75GHz':-1000, '9.4GHz':-1000}
    hdulist = iofits.open(filename)
    pheader = hdulist[0].header
    keys =[]
    for name in pheader.keys():
        keys.append(name)
    hdulist.close()
    if keys.count('DAILYF01') == 1 :
        dailyFlux['1GHz'] = pheader['DAILYF01']
    if keys.count('DAILYF02') == 1 :
        dailyFlux['2GHz'] = pheader['DAILYF02']
    if keys.count('DAILYF04') == 1 :
        dailyFlux['3.75GHz'] = pheader['DAILYF04']
    if keys.count('DAILYF09') == 1 :
        dailyFlux['9.4GHz'] = pheader['DAILYF09']
    return dailyFlux

#---norp_rd_time
#   Function for obtaining the time data from the binary extension
#   Output: List incliuded datetime objects
def norp_rd_time(filename):
    hdulist = iofits.open(filename)
    tims = hdulist[1].data['Time']
    hdulist.close()
    idlst = datetime(1979, 1, 1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    tim = []
    for timSingle in tims[0]:
        timt = datetime.fromtimestamp(timSingle+idlst.timestamp(), timezone.utc)
        tim.append(timt)
    return tim

#============= 1 GHz
#---norp_rd_1GHzI
#   Function for obtaining the 1GHz Stokes-I data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_1GHzI(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fi = hdulist[1].data['CalI_1GHz'][0]
        dv = hdulist[1].data['Dval_1GHz'][0]
        for i in range(0, fi.shape[0]):
            fi[i] = fi[i] * dv[i]
    else:
        fi = hdulist[1].data['RawI_1GHz'][0]
    hdulist.close()
    return fi

#---norp_rd_1GHzV
#   Function for obtaining the 1GHz Stokes-V data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_1GHzV(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fv = hdulist[1].data['CalV_1GHz'][0]
        dv = hdulist[1].data['Dval_1GHz'][0]
        for i in range(0, fv.shape[0]):
            fv[i] = fv[i] * dv[i]
    else:
        fv = hdulist[1].data['RawV_1GHz'][0]
    hdulist.close()
    return fv

#---norp_rd_1GHzATT
#   Function for obtaining the 1GHz ATT levels from the binary extension
def norp_rd_1GHzATT(filename):
    hdulist = iofits.open(filename)
    att = hdulist[1].data['ATT_1GHz'][0]
    hdulist.close()
    return att

#---norp_rd_1GHzSTAT
#   Function for obtaining the 1GHz STATS of the calibration from the binary extension
#   0: Sun, 1: Sky, 2: AMB, 4:Zero'
def norp_rd_1GHzSTAT(filename):
    hdulist = iofits.open(filename)
    sta = hdulist[1].data['CAL_1GHz'][0]
    hdulist.close()
    return sta

#---norp_rd_1GHzCalD
#   Function for obtaining the 1GHz values for the calibration from the binary extension
def norp_rd_1GHzCalD(filename, raw = False):
    hdulist = iofits.open(filename)
    caldt = hdulist[1].data['CALD_1GHz'][0]
    hdulist.close()
    cald ={'Scale':caldt[0], 'FISKY':caldt[1], 'FVSKY':caldt[2], \
           'FIZERO':caldt[3], 'FVZERO':caldt[4],'FIAMB':caldt[5]}
    return cald

#============= 2 GHz
#---norp_rd_2GHzI
#   Function for obtaining the 2GHz Stokes-I data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_2GHzI(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fi = hdulist[1].data['CalI_2GHz'][0]
        dv = hdulist[1].data['Dval_2GHz'][0]
        for i in range(0, fi.shape[0]):
            fi[i] = fi[i] * dv[i]
    else:
        fi = hdulist[1].data['RawI_2GHz'][0]
    hdulist.close()
    return fi

#---norp_rd_2GHzV
#   Function for obtaining the 2GHz Stokes-V data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_2GHzV(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fv = hdulist[1].data['CalV_2GHz'][0]
        dv = hdulist[1].data['Dval_2GHz'][0]
        for i in range(0, fv.shape[0]):
            fv[i] = fv[i] * dv[i]
    else:
        fv = hdulist[1].data['RawV_2GHz'][0]
    hdulist.close()
    return fv

#---norp_rd_2GHzATT
#   Function for obtaining the 2GHz ATT levels from the binary extension
def norp_rd_2GHzATT(filename, raw = False):
    hdulist = iofits.open(filename)
    att = hdulist[1].data['ATT_2GHz'][0]
    hdulist.close()
    return att

#---norp_rd_2GHzSTAT
#   Function for obtaining the 2GHz STATS of the calibration from the binary extension
#   0: Sun, 1: Sky, 2: AMB, 4:Zero'
def norp_rd_2GHzSTAT(filename, raw = False):
    hdulist = iofits.open(filename)
    sta = hdulist[1].data['CAL_2GHz'][0]
    hdulist.close()
    return sta

#---norp_rd_2GHzCalD
#   Function for obtaining the 2GHz values for the calibration from the binary extension
def norp_rd_2GHzCalD(filename, raw = False):
    hdulist = iofits.open(filename)
    caldt = hdulist[1].data['CALD_2GHz'][0]
    hdulist.close()
    cald ={'Scale':caldt[0], 'FISKY':caldt[1], 'FVSKY':caldt[2], \
           'FIZERO':caldt[3], 'FVZERO':caldt[4],'FIAMB':caldt[5]}
    return cald

#============= 3.75 GHz
#---norp_rd_4GHzI
#   Function for obtaining the 3.75GHz Stokes-I data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_4GHzI(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fi = hdulist[1].data['CalI_4GHz'][0]
        dv = hdulist[1].data['Dval_4GHz'][0]
        for i in range(0, fi.shape[0]):
            fi[i] = fi[i] * dv[i]
    else:
        fi = hdulist[1].data['RawI_4GHz'][0]
    hdulist.close()
    return fi

#---norp_rd_4GHzV
#   Function for obtaining the 3.75GHz Stokes-V data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_4GHzV(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fv = hdulist[1].data['CalV_4GHz'][0]
        dv = hdulist[1].data['Dval_4GHz'][0]
        for i in range(0, fv.shape[0]):
            fv[i] = fv[i] * dv[i]
    else:
        fv = hdulist[1].data['RawV_4GHz'][0]
    hdulist.close()
    return fv

#---norp_rd_4GHzATT
#   Function for obtaining the 3.75GHz ATT levels from the binary extension
def norp_rd_4GHzATT(filename, raw = False):
    hdulist = iofits.open(filename)
    att = hdulist[1].data['ATT_4GHz'][0]
    hdulist.close()
    return att

#---norp_rd_4GHzSTAT
#   Function for obtaining the 3.75GHz STATS of the calibration from the binary extension
#   0: Sun, 1: Sky, 2: AMB, 4:Zero'
def norp_rd_4GHzSTAT(filename, raw = False):
    hdulist = iofits.open(filename)
    sta = hdulist[1].data['CAL_4GHz'][0]
    hdulist.close()
    return sta

#---norp_rd_4GHzCalD
#   Function for obtaining the 3.75GHz values for the calibration from the binary extension
def norp_rd_4GHzCalD(filename, raw = False):
    hdulist = iofits.open(filename)
    caldt = hdulist[1].data['CALD_4GHz'][0]
    hdulist.close()
    cald ={'Scale':caldt[0], 'FISKY':caldt[1], 'FVSKY':caldt[2], \
           'FIZERO':caldt[3], 'FVZERO':caldt[4],'FIAMB':caldt[5]}
    return cald

#============= 9.4 GHz
#---norp_rd_9GHzI
#   Function for obtaining the 9.4GHz Stokes-I data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_9GHzI(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fi = hdulist[1].data['CalI_9GHz'][0]
        dv = hdulist[1].data['Dval_9GHz'][0]
        for i in range(0, fi.shape[0]):
            fi[i] = fi[i] * dv[i]
    else:
        fi = hdulist[1].data['RawI_9GHz'][0]
    hdulist.close()
    return fi

#---norp_rd_9GHzV
#   Function for obtaining the 9.4GHz Stokes-V data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_9GHzV(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fv = hdulist[1].data['CalV_9GHz'][0]
        dv = hdulist[1].data['Dval_9GHz'][0]
        for i in range(0, fv.shape[0]):
            fv[i] = fv[i] * dv[i]
    else:
        fv = hdulist[1].data['RawV_9GHz'][0]
    hdulist.close()
    return fv

#---norp_rd_9GHzATT
#   Function for obtaining the 9.4GHz ATT levels from the binary extension
def norp_rd_9GHzATT(filename, raw = False):
    hdulist = iofits.open(filename)
    att = hdulist[1].data['ATT_9GHz'][0]
    hdulist.close()
    return att

#---norp_rd_9GHzSTAT
#   Function for obtaining the 9.4GHz STATS of the calibration from the binary extension
#   0: Sun, 1: Sky, 2: AMB, 4:Zero'
def norp_rd_9GHzSTAT(filename, raw = False):
    hdulist = iofits.open(filename)
    sta = hdulist[1].data['CAL_9GHz'][0]
    hdulist.close()
    return sta

#---norp_rd_9GHzCalD
#   Function for obtaining the 9.4GHz values for the calibration from the binary extension
def norp_rd_9GHzCalD(filename, raw = False):
    hdulist = iofits.open(filename)
    caldt = hdulist[1].data['CALD_9GHz'][0]
    hdulist.close()
    cald ={'Scale':caldt[0], 'FISKY':caldt[1], 'FVSKY':caldt[2], \
           'FIZERO':caldt[3], 'FVZERO':caldt[4],'FIAMB':caldt[5]}
    return cald

#============= 17 GHz
#---norp_rd_17GHzI
#   Function for obtaining the 17GHz Stokes-I data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_17GHzI(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fi = hdulist[1].data['CalI_17GHz'][0]
        dv = hdulist[1].data['Dval_17GHz'][0]
        for i in range(0, fi.shape[0]):
            fi[i] = fi[i] * dv[i]
    else:
        fi = hdulist[1].data['RawI_17GHz'][0]
    hdulist.close()
    return fi

#---norp_rd_17GHzV
#   Function for obtaining the 17GHz Stokes-V data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_17GHzV(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fv = hdulist[1].data['CalV_17GHz'][0]
        dv = hdulist[1].data['Dval_17GHz'][0]
        for i in range(0, fv.shape[0]):
            fv[i] = fv[i] * dv[i]
    else:
        fv = hdulist[1].data['RawV_17GHz'][0]
    hdulist.close()
    return fv

#---norp_rd_17GHzATT
#   Function for obtaining the 17GHz ATT levels from the binary extension
def norp_rd_17GHzATT(filename, raw = False):
    hdulist = iofits.open(filename)
    att = hdulist[1].data['ATT_17GHz'][0]
    hdulist.close()
    return att

#---norp_rd_17GHzSTAT
#   Function for obtaining the 17GHz STATS of the calibration from the binary extension
#   0: Sun, 1: Sky, 2: AMB, 4:Zero'
def norp_rd_17GHzSTAT(filename, raw = False):
    hdulist = iofits.open(filename)
    sta = hdulist[1].data['CAL_17GHz'][0]
    hdulist.close()
    return sta

#---norp_rd_17GHzCalD
#   Function for obtaining the 17GHz values for the calibration from the binary extension
def norp_rd_17GHzCalD(filename, raw = False):
    hdulist = iofits.open(filename)
    caldt = hdulist[1].data['CALD_17GHz'][0]
    hdulist.close()
    cald ={'Scale':caldt[0], 'FISKY':caldt[1], 'FVSKY':caldt[2], \
           'FIZERO':caldt[3], 'FVZERO':caldt[4],'FIAMB':caldt[5]}
    return cald

#============= 35 GHz
#---norp_rd_35GHzI
#   Function for obtaining the 35GHz Stokes-I data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_35GHzI(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fi = hdulist[1].data['CalI_35GHz'][0]
        dv = hdulist[1].data['Dval_35GHz'][0]
        for i in range(0, fi.shape[0]):
            fi[i] = fi[i] * dv[i]
    else:
        fi = hdulist[1].data['RawI_35GHz'][0]
    hdulist.close()
    return fi

#---norp_rd_35GHzV
#   Function for obtaining the 35GHz Stokes-V data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_35GHzV(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fv = hdulist[1].data['CalV_35GHz'][0]
        dv = hdulist[1].data['Dval_35GHz'][0]
        for i in range(0, fv.shape[0]):
            fv[i] = fv[i] * dv[i]
    else:
        fv = hdulist[1].data['RawV_35GHz'][0]
    hdulist.close()
    return fv

#---norp_rd_35GHzATT
#   Function for obtaining the 35GHz ATT levels from the binary extension
def norp_rd_35GHzATT(filename, raw = False):
    hdulist = iofits.open(filename)
    att = hdulist[1].data['ATT_35GHz'][0]
    hdulist.close()
    return att

#---norp_rd_35GHzSTAT
#   Function for obtaining the 35GHz STATS of the calibration from the binary extension
#   0: Sun, 1: Sky, 2: AMB, 4:Zero'
def norp_rd_35GHzSTAT(filename, raw = False):
    hdulist = iofits.open(filename)
    sta = hdulist[1].data['CAL_35GHz'][0]
    hdulist.close()
    return sta

#---norp_rd_35GHzCalD
#   Function for obtaining the 35GHz values for the calibration from the binary extension
def norp_rd_35GHzCalD(filename, raw = False):
    hdulist = iofits.open(filename)
    caldt = hdulist[1].data['CALD_35GHz'][0]
    hdulist.close()
    cald ={'Scale':caldt[0], 'FISKY':caldt[1], 'FVSKY':caldt[2]}
    return cald

#============= 80 GHz
#---norp_rd_80GHzI
#   Function for obtaining the 80GHz Stokes-I data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the SQuareLawDetector data.
def norp_rd_80GHzI(filename, raw = False):
    hdulist = iofits.open(filename)
    if raw == False :
        fi = hdulist[1].data['CalI_80GHz'][0]
        dv = hdulist[1].data['Dval_80GHz'][0]
        for i in range(0, fi.shape[0]):
            fi[i] = fi[i] * dv[i]
    else:
        fi = hdulist[1].data['SQLD_80GHz'][0]
    hdulist.close()
    return fi

#---norp_rd_80GHzV
#   Function for obtaining the 80GHz Stokes-V data from the binary extension
#   option: raw = True/False [def. False]
#           When raw == False, the function ouputs the raw data.
def norp_rd_80GHzV(filename, raw = False):
    hdulist = iofits.open(filename)
    fv = hdulist[1].data['CalV_80GHz'][0]
    dv = hdulist[1].data['Dval_80GHz'][0]
    for i in range(0, fv.shape[0]):
        fv[i] = fv[i] * dv[i]
    hdulist.close()
    return fv

#---norp_rd_80GHzATT
#   Function for obtaining the 80GHz ATT levels from the binary extension
def norp_rd_80GHzATT(filename, raw = False):
    hdulist = iofits.open(filename)
    att = hdulist[1].data['ATT_80GHz'][0]
    hdulist.close()
    return att

#---norp_rd_35GHzSTAT
#   Function for obtaining the 35GHz STATS of the calibration from the binary extension
#   0: Sun, 1: Sky, 2: AMB, 4:Zero'
def norp_rd_80GHzSTAT(filename, raw = False):
    hdulist = iofits.open(filename)
    sta = hdulist[1].data['CAL_80GHz'][0]
    hdulist.close()
    return sta

#=================norp_plot_summary===
#   Function makes the summary plot of the NoRP FITS file
#   Option: savepng=True/False [def. False]
#   When savepng == True, the function creates the PNG file of the plot.
def norp_plot_summary(filename, savepng=False, dir='.'):
    obsDay = norp_rd_obsDay(filename)
    tim = norp_rd_time(filename)
    exFq = norp_rd_existFreq(filename)

    fig = plt.figure(figsize=(20, 20), tight_layout=True)
    ax01 = fig.add_subplot(7, 2, 1,ylabel='Flux [SFU]', title='NoRP 1GHz Stokes-I on '+obsDay+'[JST]')
    ax03 = fig.add_subplot(7, 2, 3,ylabel='Flux [SFU]', title='NoRP 2GHz Stokes-I')
    ax05 = fig.add_subplot(7, 2, 5,ylabel='Flux [SFU]', title='NoRP 3.75GHz Stokes-I')
    ax07 = fig.add_subplot(7, 2, 7,ylabel='Flux [SFU]', title='NoRP 9.4GHz Stokes-I')
    ax09 = fig.add_subplot(7, 2, 9,ylabel='Flux [SFU]', title='NoRP 17GHz Stokes-I')
    ax11 = fig.add_subplot(7, 2, 11,ylabel='Flux [SFU]', title='NoRP 35GHz Stokes-I')
    ax13 = fig.add_subplot(7, 2, 13,ylabel='Flux [SFU]', title='NoRP 80GHz Stokes-I', xlabel='Time[UT]')

    ci,cv = 'blue','orange'

    if exFq['1GHz'] == 1:
        fi01 = norp_rd_1GHzI(filename)

        ax01.set_ylim(10, np.max(fi01)*1.1)
        ax01.plot(tim, fi01, marker=".", linestyle='None', markersize=0.2, color=ci)
        ax01axes = ax01.xaxis
        ax01axes.set_major_formatter(DateFormatter('%H:%M'))
    else:
        ax01.text(0.35, 0.4, 'No Data', fontsize=20)


    if exFq['2GHz'] == 1:
        fi02 = norp_rd_2GHzI(filename)

        ax03.set_ylim(10, np.max(fi02)*1.1)
        ax03.plot(tim, fi02, marker=".", linestyle='None', markersize=0.2, color=ci)
        ax03axes = ax03.xaxis
        ax03axes.set_major_formatter(DateFormatter('%H:%M'))

    else:
        ax03.text(0.35, 0.4,'No Data', fontsize=20)


    if exFq['3.75GHz'] == 1:
        fi04 = norp_rd_4GHzI(filename)
        ax05.set_ylim(10, np.max(fi04)*1.1)
        ax05.plot(tim, fi04, marker=".", linestyle='None', markersize=0.2, color=ci)
        ax05axes = ax05.xaxis
        ax05axes.set_major_formatter(DateFormatter('%H:%M'))

    else:
        ax05.text(0.35, 0.4,'No Data', fontsize=20)

    if exFq['9.4GHz'] == 1:
        fi09 = norp_rd_9GHzI(filename)
        ax07.set_ylim(10, np.max(fi09)*1.1)
        ax07.plot(tim, fi09, marker=".", linestyle='None', markersize=0.2, color=ci)
        ax07axes = ax07.xaxis
        ax07axes.set_major_formatter(DateFormatter('%H:%M'))
        
    else:
        ax07.text(0.35, 0.4,'No Data', fontsize=20)

    if exFq['17GHz'] == 1:
        fi17 = norp_rd_17GHzI(filename)

        ax09.set_ylim(np.min(fi17)*0.5, np.max(fi17)*1.1)
        ax09.plot(tim, fi17, marker=".", linestyle='None', markersize=0.2, color=ci)
        ax09axes = ax09.xaxis
        ax09axes.set_major_formatter(DateFormatter('%H:%M'))

    else:
        ax09.text(0.35, 0.4,'No Data', fontsize=20)

    if exFq['35GHz'] == 1:
        fi35 = norp_rd_35GHzI(filename)

        ax11.set_ylim(np.max(fi35)*0.5, np.max(fi35)*1.1)
        ax11.plot(tim, fi35, marker=".", linestyle='None', markersize=0.2, color=ci)
        ax11axes = ax11.xaxis
        ax11axes.set_major_formatter(DateFormatter('%H:%M'))

    else:
        ax11.text(0.35, 0.4,'No Data', fontsize=20)


    if exFq['80GHz'] == 1:
        fi80 = norp_rd_80GHzI(filename)

        ax13.set_ylim(np.max(fi80)*0.5, np.max(fi80)*1.1)
        ax13.plot(tim, fi80, marker=".", linestyle='None', markersize=0.2, color=ci)
        ax13axes = ax13.xaxis
        ax13axes.set_major_formatter(DateFormatter('%H:%M'))

    else:
        ax13.text(0.35, 0.4,'No Data', fontsize=20)

    if savepng == True:
        fig.savefig(dir+"/norp_plot_"+obsDay+".png")
    else:
        plt.show()      

    plt.close()
