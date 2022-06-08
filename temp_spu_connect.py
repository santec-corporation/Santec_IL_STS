import clr
ans = clr.AddReference(r'./DLL/STSProcess')


ans = clr.AddReference(r'./DLL/InstrumentDLL')

ans2 = clr.AddReference(r'./DLL/NationalInstruments.DAQmx')
from Santec import SPU
spu= SPU()
spu.DeviceName = 'Dev3'
spu.Connect('')