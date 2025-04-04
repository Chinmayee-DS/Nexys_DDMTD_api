#!/home/pi/ddmtd_running/env/bin/python

# pip install pandas matplotlib scipy numpy

import pandas as pd
import numpy as np
from tools.base import *
from tools.ddmtd import *
from tools.tool import *
import datetime
import os
import yaml
import sys
import importlib

def calculate(n_val, ipf):
    # data_folder = "./data"
    data_folder = "./../Flash_Firmware/data"
    # dv1= pd.read_csv("{0}/ddmtd1.txt".format(data_folder),sep=",",header=0 ,skiprows=0,names=['edge','ddmtd'])
    # dv2= pd.read_csv("{0}/ddmtd2.txt".format(data_folder),sep=",",header=0 ,skiprows=0,names=['edge','ddmtd'])
    dv1= pd.read_csv("{0}/ddmtd1.txt".format(data_folder),sep=",",header=None ,skiprows=0,names=['edge','ddmtd'])
    dv2= pd.read_csv("{0}/ddmtd2.txt".format(data_folder),sep=",",header=None ,skiprows=0,names=['edge','ddmtd'])
    # print("{0}/ddmtd1.txt".format(data_folder))
    # print(dv1.head())
    df1_c = clean_data(dv1,mode=1)
    df2_c = clean_data(dv2,mode=1)
    # print(df1_c.head())
    # print(df2_c.head())

    def make_falling_edge(df,mode=1):
        # if df[f"falling_edge{mode}"].values[0] == 0: # drop the first edge
            # df = df.iloc[1:]
        # df = df [df["falling_edge{mode}".format(mode)] == 1]
        df = df[df[f"falling_edge{mode}"] == 1]
        return df.reset_index(drop=True)

    df1_c = make_falling_edge(df1_c,mode=1)
    df2_c = make_falling_edge(df2_c,mode=1)


    # print(df1_c)
    # print(df2_c)


    # N=100000
    N=int(n_val)
    # INPUT_FREQ = 160*10**6
    # INPUT_FREQ = 40*10**6
    # INPUT_FREQ = int(float(inp_freq))*10**6
    INPUT_FREQ = int(float(ipf))*10**6
    # print(N)
    # print(INPUT_FREQ)
    # INPUT_FREQ = 640*10**6
    FREQ = (1.0*N)/(N+1)*INPUT_FREQ
    MEASURE_FREQ = FREQ
    MEASURE_PERIOD = 1.*10**9/MEASURE_FREQ# ns
    PERIOD =  1.0*10**9/FREQ # ns
    BEAT_FREQ = 1.*INPUT_FREQ/(N+1)
    BEAT_PERIOD = 1./BEAT_FREQ
    MULT_FACT = MEASURE_PERIOD*10**(-9)/(N+1)*10**9


    TIE_rise = (df1_c.avg1 - df2_c.avg1)
    TIE_rise.dropna(inplace=True)
    # print(TIE_rise)
    rise_mean = TIE_rise.mean()*MULT_FACT*1000 #ps
    rise_std  = TIE_rise.std()*MULT_FACT*1000  #ps
    rise_size = TIE_rise.size
    dt = datetime.datetime.now(datetime.timezone.utc) 
    utc_time = dt.replace(tzinfo=datetime.timezone.utc) 
    utc_timestamp = utc_time.timestamp() 

    # pico_factor = (1/inp_freq) * 1000000
    pico_factor = (1/int(float(ipf))) * 1000000
    print(pico_factor)
    # return utc_timestamp,rise_mean % 6250,rise_std,rise_size #ps
    return utc_timestamp,rise_mean % pico_factor,rise_std,rise_size #ps

# uncomment here
# import time
# import subprocess

# holdVal = 0
# # for i in range(2600):
# # no_ite = sys.argv[2]
# # N = sys.argv[1]
# # inp_freq = sys.argv[3]
# # print("Number_of_iterations " + str(no_ite))
# # print("N value " + str(N))
# # print("Input Frequency " + str(inp_freq))
# with open("output.txt", "w") as f:
#     pass

# for i in range(int(no_ite)):
#     # os.system("sudo ./data_acq.exe")
#     # subprocess.run(["sudo", "./../Flash_Firmware/bin/data_acq.exe"], shell=False)
#     #subprocess.run(['./shiftpll.sh','1','1'], check=True)
#     # result = subprocess.run("sudo ./data_acq.exe", shell=True, capture_output=True, text=True)
#     # result = subprocess.run("cd ./../Flash_Firmware && sudo ./bin/data_acq.exe", shell=True, capture_output=True, text=True)
#     # command = ["cd", "~/Flash_Firmware", "&&", "sudo", "./bin/data_acq.exe"]
#     # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
#     command = "cd ~/Flash_Firmware && sudo ./bin/data_acq.exe"
#     process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)

#     stdout, stderr = process.communicate()
#     # print("Output:", stdout)
#     # print("Error:", stderr)
#     # print("Return Code:", result.returncode)
#     # print(i)
#     time.sleep(1)
#     # out = calculate()
#     out = calculate(N)
    
#     f = open("output.txt", "a")
#     # print(",".join( [str(i) for i in out] ))
#     f.write(",".join( [str(i) for i in out]) + "\n")
#     f.close()
#     time.sleep(1)

#     # time.sleep(1)

#     # break
# end uncomment here


#OLD CODE...
# dv1= pd.read_csv(f"{data_folder}/ddmtd1.txt",sep=",",header=0 ,skiprows=0,names=['edge1','ddmtd1'])
# dv2= pd.read_csv(f"{data_folder}/ddmtd2.txt",sep=",",header=0 ,skiprows=0,names=['edge2','ddmtd2'])
# dv = pd.concat((dv1,dv2),axis=1) 
# data = ddmtd(dv,q=1,channel=(1,2))
# data.N=100_000
# data.INPUT_FREQ = 160*10**6
# data.Recalc()
# df = data
# y = df.TIE_rise*df.MULT_FACT
# std_y = np.std(y)*1000 #ps
# mean_y = np.mean(y)*1000 #ps
# size_y = y.size

# print(mean_y,std_y,size_y)