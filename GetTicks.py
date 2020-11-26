import requests
import json
import re

if __name__ == "__main__":
    url = 'http://localhost:8080/Ticks'
    myobj = {'somekey': 'somevalue'}

    pattern = "([0-9]+): Date: ([0-9]+), Open: ([\\-0-9\\.]+), High: ([\\-0-9\\.]+), Low: ([\\-0-9\\.]+), Close: ([\\-0-9\\.]+), Volume: ([\\-0-9\\.]+), Average: ([\\-0-9\\.]+), BarCount: ([\\-0-9\\.]+)"
    x = requests.post(url, data = myobj)
    mt = re.findall(pattern, x.text)
    #print("{}".format(mt))
    for m in mt:
        print("Date: {}, Open: {}, High: {}, Low: {}, Close: {}, Volume: {}, Average: {}, BarCount: {}"
            .format(m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8]))


'''

['Market data farm connection is OK:usfarm.nj',
 'Market data farm connection is OK:cashfarm',
 'Market data farm connection is OK:usfarm',
 'HMDS data farm connection is OK:euhmds',
 'HMDS data farm connection is OK:cashhmds',
 'HMDS data farm connection is OK:ushmds',
 'Sec-def data farm connection is OK:secdefil',
 1696454136832:
 Date: 20200430, Open: 0.872395, High: 0.874280, Low: 0.867110, Close: 0.869805, Volume: -1, Average: -1.000000, BarCount: -1,
 1696458471360:
 Date: 20200501, Open: 0.869850, High: 0.879675, Low: 0.869155, Close: 0.877730, Volume: -1, Average: -1.000000, BarCount: -1,
 1696458471408:
 Date: 20200504, Open: 0.878605, High: 0.881440, Low: 0.875450, Close: 0.876375, Volume: -1, Average: -1.000000, BarCount: -1,
 1696458471456:
 Date: 20200505, Open: 0.876300, High: 0.876705, Low: 0.869060, Close: 0.871350, Volume: -1, Average: -1.000000, BarCount: -1,
 1696458471504:
 Date: 20200506, Open: 0.871440, High: 0.875695, Low: 0.869805, Close: 0.874790, Volume: -1, Average: -1.000000, BarCount: -1,
 1696458471552:
 Date: 20200507, Open: 0.875050, High: 0.878990, Low: 0.870880, Close: 0.876170, Volume: -1, Average: -1.000000, BarCount: -1,
 1696458471600:
 Date: 20200508, Open: 0.876325, High: 0.876860, Low: 0.871275, Close: 0.873565, Volume: -1, Average: -1.000000, BarCount: -1, 1696458471648: Date: 20200511, Open: 0.872850, High: 0.880695, Low: 0.872150, Close: 0.876200, Volume: -1, Average: -1.000000, BarCount: -1, 1696458471696: Date: 20200512, Open: 0.876600, High: 0.885175, Low: 0.875880, Close: 0.884820, Volume: -1, Average: -1.t: -1, 1696458471792: Date: 20200514, Open: 0.884075, High: 0.887125, Low: 0.882610, Close: 0.883305, Volume: -1, Average: -1.000000, BarCount: -1, 1696458471840: Date: 20200515, Open: 0.883975, High: 0.893985, Low: 0.882940, Close: 0.893730, Volume: -1, Average: -1.000000, BarCount: -1, 1696458471888: Date: 20200518, Open: 0.895350, High: 0.896425, Low: 0.889430, Close: 0.895135, Volume: -1, Average: -1.000000, BarCount: -1, 1696458471936: Date: 20200519, Open: 0.895150, High: 0.895765, Low: 0.890250, Close: 0.891590, Volume: -1, Average: -1.000000, BarCount: -1, 1696458471984: Date: 20200520, Open: 0.891930, High: 
e: -1.000000, BarCount: -1, 1696458472224: Date: 20200527, Open: 0.890225, High: 0.899415, Low: 0.888925, Close: 0.897710, Volume: -1, Average: -1.000000, BarCount: -1, 1696458472272: Date: 20200528, Open: 0.897700, High: 0.899440, Low: 0.896335, Close: 0.899035, Volume: -1, Average: -1.000000, BarCount: -1, 1696458472320: Date: 20200529, Open: 0.898675, High: 0.905475, Low: 0.897950, Close: 0.899215, Volume: -1, Average: -1.000000, BarCount: -1]

'''
