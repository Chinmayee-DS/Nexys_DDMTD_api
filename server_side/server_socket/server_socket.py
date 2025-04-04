import subprocess
import os
import socket
import mmap
import ctypes
import yaml
import re
import time
import sys
sys.path.append("/home/pi/Flash_Firmware")
from get_data import *

CHUNKSIZE = 1024
CURRENT_CONFIG_FILE = "/home/pi/PLL_config/pll_config_100000_160MHz_1.341kHz_2.687kHz.yaml" #some file
PREVIOUS_CONFIG_FILE = "/home/pi/PLL_config/pll_config_10000_40.079MHz_663.277Hz_663.277Hz.yaml" #some file
n_pattern = r'OUT1:\s*.*\[\s*\d+\s*\+\s*\d+/(\d+)\s.*\]'
nom_pattern = r'Actual:\s*([\d]+(\.[\d]+)?)\s*(\w+)'
inp_pattern = r'IN1:\s*(\d+(\.\d+)?)\s*(\w+)'

def exec_com(command, resp, flag = 0):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    if process.returncode == 0:
        print(stdout)

        if flag == 1:
            if stdout[-2] == '2':
                resp = resp + "The uploaded PLL configuration is for the hardware is Si5344C.\n"
            elif stdout[-2] == '7':
                resp = resp + "The uploaded PLL configuration is for the hardware is Si5344H.\n"
        else:
            resp = resp + stdout + "\n"

    else:
        print("Command failed with return code:", process.returncode)
        print(stderr)
        resp = resp + stderr + "\n"
    
    if flag == 2:
        if process.returncode == 0:
            return resp, stdout
        else:
            return resp, "Error"

    else:
        return resp

def receive_directory(sock, f_n):
    clientfile = sock.makefile('rb')
    try:
        while True:
            raw = clientfile.readline()
            if raw.strip().decode() == "No more files":
                break

            filename = raw.strip().decode()
            length = int(clientfile.readline())
            path = os.path.join(f_n,filename)

            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))

            # Read the data in chunks so it can handle large files.
            with open(path,'wb') as f:
                while length:
                    chunk = min(length,CHUNKSIZE)
                    data = clientfile.read(chunk)
                    if not data: break
                    f.write(data)
                    length -= len(data)
                else: # only runs if while doesn't break and length==0
                    print('Complete')
                    continue

            # socket was closed early.
            print('Incomplete')
            break
    except Exception as e:
        print('Error recieving files - ', e)

def api_1(conn):
    """Handles the Firmware API."""
    while True:
        conn.send(b"Flash Firmware - Choose an option:\n \
        1. Upload firmware :\n \
        2. List all available firmware versions\n \
        3. Select firmware to flash:\n \
        4. Check the firmware version:\n \
        5. Restart FPGA:\n \
        6. Enter PLL configuration info\n")

        try:
            data = conn.recv(CHUNKSIZE).decode()
        except Exception as e:
            print('Error recieveing option from client:', e)

        if data == "1":
            response = ""
            try:
                conn.send(b"Processing")
                folder_n = conn.recv(CHUNKSIZE).decode()
                save_directory = '/home/pi/'
                # save_directory = '/home/pi/server_socket/'
                save_directory = save_directory + folder_n
                receive_directory(conn, save_directory)
                response = response + "Recieved the files successfully\n"
            except Exception as e:
                print('Error handling client:', e)
                response = response + "Error in recieving files " + e
            
            conn.send(response.encode())
            conn.recv(1024).decode()

        elif data == "2":
            response = ""
            try:
                files = os.listdir('../Flash_Firmware/HEX_Files')
                response = "\n".join(files) if files else "No files available."
            except Exception as e:
                print("Error displaying files in the ../Flash_Firmware/HEX_Files directory ", e)
                response = response + "Error displaying files in the ../Flash_Firmware/HEX_Files directory " + e
            conn.send(response.encode())
            conn.recv(1024).decode()

        elif data == "3":
            resp = ""
            try:
                files = os.listdir('../Flash_Firmware/HEX_Files')
                response = "\n".join("{0}: {1}".format(index+1, file) for index, file in enumerate(files)) if files else "No files available."
                conn.sendall(response.encode())
                fw_to_flash = conn.recv(CHUNKSIZE).decode()
                fw_to_flash_num = int(fw_to_flash)
                flag = 0
                # print(files[fw_to_flash_num - 1])
                command = ["bash" ,"./Flash_fw.sh", files[fw_to_flash_num - 1]]
                # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                # stdout, stderr = process.communicate()
                # if process.returncode == 0:
                #     print(stdout)
                #     resp = resp + stdout
                # else:
                #     print("Command failed with return code:", process.returncode)
                #     print(stderr)
                #     resp = resp + stderr
                #     # flag = 1
                resp = exec_com(command, resp)
            except Exception as e:
                print("Error executing this functionality ", e)
                resp = resp + "Error occured " + e
            # command = ["bash", "./runNex.sh", "../restart_FPGA.sh", "0", "0"]
            # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            # stdout, stderr = process.communicate()
            # if process.returncode == 0 and flag == 0:
            #     print("Command executed successfully.")
            #     print("Output:")
            #     print(stdout)  # Standard output
            #     resp = resp + stdout
            #     # resp = resp + "\nDone, success"
            #     resp = resp + "\n"
            #     # print(type(stdout))
            # else:
            #     print("Command failed with return code:", process.returncode)
            #     print("Error:")
            #     print(stderr)  # Standard error
            #     resp = resp + stderr + "\n"
            conn.send(resp.encode())
            conn.recv(1024).decode()

        elif data == "4":
            resp = ""
            try:
                command = ['bash', "./runNex.sh", "bin/check_firmware.exe", "0", "1"]
                resp = exec_com(command, resp)
                # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                # stdout, stderr = process.communicate()
                # if process.returncode == 0:
                #     print(stdout)  # Standard output
                #     resp = resp + stdout
                #     resp = resp + "\n"
            
                # else:
                #     print("Command failed with return code:", process.returncode)
                #     print(stderr)  # Standard error
                #     resp = resp + stderr + "\n"
        
            except Exception as e:
                print("Error running check_firmware, please check the availability of files ", e)
                resp = resp + "Error occured " + e

            conn.send(resp.encode())
            conn.recv(1024).decode()

        elif data == "6":
            try:
                conn.send(b"Enter PLL configuration information\n")
                conn.recv(1024).decode()
            except Exception as e:
                print("Error in communication with client ", e)
            return api_2(conn)

        else:
            try:
                conn.send(b"Invalid option. Try again.")
                conn.recv(1024).decode()
            except Exception as e:
                print("Error in communication with client ", e)

def api_2(conn):
    """Handles the PLL API."""
    while True:
        conn.send(b"PLL config: Choose an option: \
        \n7. Fetch current config file \
        \n8. Fetch the previous config file \
        \n9. Display and see all the contents of the config files \
        \n10. Use an existing config or upload config file \
        \n11. Move to API 3. \
        \n12. Move to API 1 \n")
        try:
            data = conn.recv(CHUNKSIZE).decode()
        except Exception as e:
            print('Error recieveing option from client:', e)

        if data == "7":
            resp = ""
            try:
                command = ["cat", globals()["CURRENT_CONFIG_FILE"]]
                resp = exec_com(command, resp)
                # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                # stdout, stderr = process.communicate()
                # if process.returncode == 0:
                #     print(stdout)  # Standard output
                #     resp = resp + stdout + "\n"
                    
                # else:
                #     print("Command failed with return code:", process.returncode)
                #     print(stderr)  # Standard error
                #     resp = resp + stderr + "\n"
            except Exception as e:
                print("Error running fetching current config file, please check the availability of files ", e)
                resp = resp + "Error occured " + e

            conn.send(resp.encode())
            conn.recv(1024).decode()

        elif data == "8":
            resp = ""
            try:
                command = ["cat", globals()["PREVIOUS_CONFIG_FILE"]]
                resp = exec_com(command, resp)
                # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                # stdout, stderr = process.communicate()
                # if process.returncode == 0:
                #     print(stdout)  # Standard output
                #     resp = resp + stdout
                #     resp = resp + "\n"

                # else:
                #     print("Command failed with return code:", process.returncode)
                #     print(stderr)  # Standard error
                #     resp = resp + stderr + "\n"
            except Exception as e:
                print("Error running fetching previous config file, please check the availability of files ", e)
                resp = resp + "Error occured " + e

            conn.send(resp.encode())
            conn.recv(1024).decode()

        elif data == "10":
            resp = ""
            try:
                directory = "/home/pi/PLL_config"
                files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
                response = "\n".join("{0}: {1}".format(index+1, file) for index, file in enumerate(files)) if files else "No files available."
                response = response + "\nEnter 0 to upload a new config file\n"

                conn.sendall(response.encode())
                pll_to_flash = conn.recv(CHUNKSIZE).decode()
                pll_to_flash = int(pll_to_flash)
            except Exception as e:
                print("Error ", e)
                resp = resp + "Error " + e

            if pll_to_flash == 0:
                raw = conn.recv(CHUNKSIZE)
                recd = raw.strip().decode()
                recd_data = recd.split()
                filename = recd_data[0]
                filename = filename.split('/')[-1]
                fp = "./../PLL_config/config_fold/" + filename
                length = int(recd_data[1])
                loc_flag = 0
                with open(fp, 'wb') as file:
                    while length > 0:
                        chunk = min(length, CHUNKSIZE)
                        data = conn.recv(chunk)
                        if not data:
                            print("Error: Received empty data. Connection may be closed.")
                            resp = resp + "Error: Received empty data. Connection may be closed.\n"
                            conn.sendall(response.encode())
                            loc_flag = 1
                            break
                        file.write(data)
                        length -= len(data)
                if loc_flag == 1:
                    continue
                flag = 0
                globals()["PREVIOUS_CONFIG_FILE"] = globals()["CURRENT_CONFIG_FILE"]
                try:
                    with open(fp, 'r') as file:
                        for line in file:
                            if flag == 0:
                                match = re.search(inp_pattern, line)
                                print("1.here")
                                if match:
                                    flag = flag + 1
                                    inp_freq = match.group(1) + match.group(3)
                                    num_inp_freq = match.group(1) + "_" + match.group(3)
                            elif flag == 1:
                                match = re.search(n_pattern, line)
                                if match:
                                    print("2.here")
                                    flag = flag + 1
                                    N_val = match.group(1)
                            elif flag == 2:
                                match = re.search(nom_pattern, line)
                                if match:
                                    print("3.here")
                                    flag = flag + 1
                                    nom_freq = match.group(1) + match.group(3)
                            elif flag == 3:
                                match = re.search(nom_pattern, line)
                                if match:
                                    print("4.here")
                                    flag = flag + 1
                                    fast_freq = match.group(1) + match.group(3)
                                    break
                    print(inp_freq)
                    print(nom_freq)
                    print(fast_freq)
                    print(N_val)
                except Exception as e:
                    print("Error occured when trying to extract variables from configuration file ", e)
                    resp = resp + "Error occured in configuration file. Please check if the file is correct " + e
                
                output_yaml_file = "pll_config_" + str(int(N_val)-1) + "_" + inp_freq + "_" + nom_freq + "_" + fast_freq
                data_to_save = {
                    'filename': fp, #or filename either works but okay lets see
                    'N_val': int(N_val) - 1,
                    'nom_freq': nom_freq,
                    'fast_freq': fast_freq,
                    'input_freq': num_inp_freq
                }
                save_file = "./../PLL_config/" + output_yaml_file + ".yaml"
                # Write data to YAML file
                try:
                    with open(save_file, 'w') as yaml_file:
                        yaml.dump(data_to_save, yaml_file, default_flow_style=False)
                except Exception as e:
                    print("Error when saving file as yaml ", e)
                    resp = resp + "Error when saving the yaml file " + e
                # extract the N, input_freq and nominal freq from the file.
                
                globals()["CURRENT_CONFIG_FILE"] = save_file

            else:
                with open("./../PLL_config/" + files[pll_to_flash-1], 'r') as file:
                    try:
                        contents = yaml.safe_load(file)  # Load the contents of the YAML file
                    except yaml.YAMLError as e:
                        print(f"Error reading YAML file: {e}")
                        resp = resp + "Error reading YAML file"
                        continue
                fp = contents["filename"]
                
                globals()["CURRENT_CONFIG_FILE"] = "./../PLL_config/" + files[pll_to_flash-1]
            
            try:
                dest = "./../Flash_Firmware/include/Si5344_REG.h"
                command = ["cp", fp, dest]
                resp = exec_com(command, resp)
                # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                # stdout, stderr = process.communicate()
                # if process.returncode == 0:
                #     print("Command executed successfully.")
                #     print("Output:")
                #     print(stderr)  # Standard output
                #     resp = resp + stdout + "\n"
                # else:
                #     print("Command failed with return code:", process.returncode)
                #     print("Error:")
                #     print(stderr)  # Standard error
                #     resp = resp + stderr + "\n"
            except Exception as e:
                print("Error in copying the configuration file. ", e)
                resp = resp + "Error in copying the configuration file. " + e

            try:
                command = ['bash', "./runNex.sh", "bin/ddmtd_pll.exe", "1", "1"]
                resp = exec_com(command, resp)
                # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                # stdout, stderr = process.communicate()
                # if process.returncode == 0:
                #     print("Command executed successfully.")
                #     print("Output:")
                #     print(stdout)  # Standard output
                #     resp = resp + stdout + "\n"
            
                # else:
                #     print("Command failed with return code:", process.returncode)
                #     print("Error:")
                #     print(stderr)  # Standard error
                #     resp = resp + stderr + "\n"
            except Exception as e:
                print("Error when trying to compile pll. Check the pll file for the appropriate hardware. ", e)
                resp = resp + "Error when trying to compile pll. Check the pll file for the appropriate hardware" + e
            
            try:
                # command = ["gcc", "-Iinclude", "-O", "Flash_Firmware/src/check_hardware.c Flash_Firmware/src/spi_common.c", "Flash_Firmware/src/NexysDDMTD.c", "-l", "Flash_Firmware/bcm2835", "-o", "Flash_Firmware/bin/check_hardware.exe"]
                # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                command = ["sudo", "../Flash_Firmware/bin/check_hardware.exe"]
                resp = exec_com(command, resp, 1)
                # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                # stdout, stderr = process.communicate()
                # if process.returncode == 0:
                #     print("Command executed successfully.")
                #     print("Output:")
                #     print(stdout)  # Standard output
                    
                # else:
                #     print("Command failed with return code:", process.returncode)
                #     print("Error:")
                #     print(stderr)  # Standard error
                #     resp = resp + stderr + "\n"

                # if stdout[-2] == '2':
                #     resp = resp + "The uploaded PLL configuration is for the hardware is Si5344.\n"
                # elif stdout[-2] == '7':
                #     resp = resp + "The uploaded PLL configuration is for the hardware is Si5344H.\n"
            except Exception as e:
                print("Error in checking the hardware type ", e)
                resp = resp + "Error in checking the hardware type " + e

            conn.send(resp.encode())
            conn.recv(1024).decode()

        elif data == "11":
            try:
                conn.send(b"Moving to API 3.\n")
                conn.recv(1024).decode()
            except Exception as e:
                print("Error in communication with client ", e)
            return api_3(conn)  # Move to API 3

        elif data == "12":
            try:
                conn.send(b"Moving to API 1.\n")
                conn.recv(1024).decode()
            except Exception as e:
                print("Error in communication with client ", e)
            return api_1(conn)

        elif data == "9":
            resp_temp = ""
            directory = "/home/pi/PLL_config"
            try:
                files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            except Exception as e:
                print("Error in listing files frim /home/pi/PLL_config directory. ", e)
                resp_temp = "Error in listing files frim /home/pi/PLL_config directory. " + e

            while True:
                try:
                    resp = resp_temp
                    response = ""
                    response = "\n".join("{0}: {1}".format(index+1, file) for index, file in enumerate(files)) if files else "No files available."
                    response = response + "\nEnter 0 to return to menu\n"

                    conn.sendall(response.encode())
                    user_opt = conn.recv(CHUNKSIZE).decode()
                    user_opt = int(user_opt)
                except Exception as e:
                    print("Error in displaying files or recieveing input from user ", e)
                    resp = resp + "Error in displaying files or recieveing input from user " + e
                
                if user_opt == 0:
                    conn.send(b"Returning to main menu")
                    break

                elif user_opt <= len(files):
                    command = ["cat", "./../PLL_config/" + files[user_opt-1]]
                    resp = exec_com(command, resp)
                    # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                    # stdout, stderr = process.communicate()
                    # if process.returncode == 0:
                    #     print("Command executed successfully.")
                    #     print("Output:")
                    #     print(stdout)  # Standard output
                    #     resp = resp + stdout + "\n"

                    # else:
                    #     print("Command failed with return code:", process.returncode)
                    #     print("Error:")
                    #     print(stderr)  # Standard error
                    #     resp = resp + stderr + "\n"

                    conn.send(resp.encode())
                
                else:
                    resp = resp + "Choose a valid option\n"
                    conn.send(resp.encode())
                
            conn.recv(1024).decode()

        else:
            try:
                conn.send(b"Invalid option. Try again.\n")
                conn.recv(1024).decode()
            except Exception as e:
                print("Error in communication with client ", e)

def api_3(conn):
    """Handles the Computation API."""
    while True:
        conn.send(b"Data Acquisiton: Choose an option: \
        \n13. Fetch the raw data(ddmtd1.txt, ddmtd2.txt) \
        \n14. Compute the phase difference for n iterations \
        \n15. Return to PLL API \
        \n16. Close connection to the server\n")

        try:
            data = conn.recv(CHUNKSIZE).decode()
        except Exception as e:
            print('Error recieveing option from client:', e)

        if data == "13":
            resp = ""
            try:
                command = ["sudo", "../Flash_Firmware/bin/new_da.exe"]
                resp, op = exec_com(command, resp, 2)
                buf = 0
                output = op.splitlines()
                buf = int(output[-1])
                # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                # stdout, stderr = process.communicate()
                # buf = 0
                # if process.returncode == 0:
                #     print(stdout)  # Standard output
                #     resp = resp + stdout + "\n"
                #     output = stdout.splitlines()
                #     buf = int(output[-1])
                    
                # else:
                #     print("Command failed with return code:", process.returncode)
                #     print(stderr)  # Standard error
                #     resp = resp + stderr + "\n"
            
            except Exception as e:
                print("Error in acquiring data. ", e)
                resp = resp + "Error in acquiring data " + e

            SHM_NAME = "/dev/shm/my_shared_memory"
            BUFFER_SIZE = buf
            
            try:
                shm_fd = os.open(SHM_NAME, os.O_RDONLY)
                mm = mmap.mmap(shm_fd, BUFFER_SIZE, access=mmap.ACCESS_READ)
                # Read the data
                data = mm.read(BUFFER_SIZE)

                # Clean up
                mm.close()
                os.close(shm_fd)
            except Exception as e:
                print("Error in accessing shared memory space ", e)
                resp = resp + "Error in accessing data acquired " + e

            try:
                # command = ["gcc", "-o", "../Flash_Firmware/bin/unl", "../Flash_Firmware/src/unl.c", "-lrt"]
                # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                # stdout, stderr = process.communicate()
                # print(stdout)
                # print(stderr)
                command = ["sudo", "../Flash_Firmware/bin/unl"]
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    print("Uncsuccessful unlink")
                    resp = resp + "Unsuccessful unlink of shared memory\n"

            except Exception as e:
                print("Error in unlinking shared memory ", e)
                resp = resp + "Error in unlinking shared memory, will cause memory issues in future. " + e

            try:
                conn.send(str(buf).encode())
                chunk_size = 4096

                # Send the data in chunks
                for i in range(0, len(data), chunk_size):
                    chunk = data[i:i + chunk_size]  # Get the current chunk
                    conn.send(chunk)

                print("HEre I am")
                conn.recv(CHUNKSIZE).decode()
                conn.send(resp.encode())
                conn.recv(1024).decode()
            except Exception as e:
                print("Error in sending data files to client ", e)
                resp = resp + "Error in sending data files to client " + e

        elif data == "14":
            resp = ""
            try:
                no_ite = conn.recv(CHUNKSIZE).decode()
                no_ite = int(no_ite)
                
                with open(globals()["CURRENT_CONFIG_FILE"], 'r') as file:
                    contents = yaml.safe_load(file)
            except Exception as e:
                print("Error in accessing current config yaml file. ", e)
                resp = resp + "Error in accessing current config yaml file. Please ensure the correct PLL configuration file is flashed " + e
            
            N_val = contents["N_val"]
            inp_freq = contents["input_freq"]
            num_inp_freq = inp_freq.split('_')[0]
            # new c
            for i in range(no_ite):
                resp = ""
                command = "cd ~/Flash_Firmware && sudo ./bin/data_acq.exe"
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)

                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    print("Command failed with return code:", process.returncode)
                    print("Error:")
                    print(stderr)  # Standard error
                    resp = resp + stderr + "\nFailed on " + (i+1) + "th iteration\n"
                    conn.send(resp.encode())
                    break

                time.sleep(1)
                
                try:
                    out = calculate(N_val, num_inp_freq)
                    print(",".join([str(i) for i in out]) + "\n")
                    resp = resp + ",".join([str(i) for i in out]) + "\n"
                except Exception as e:
                    print("Error in calculating the phase difference ", e)
                    resp = resp + "Error in calculating the phase difference. Ensure hardware is connected properly. " + e
                conn.send(resp.encode())

            # end new c
            conn.recv(1024).decode()

        elif data == "15":
            try:
                conn.send(b"Moving to API 2.\n")
                conn.recv(1024).decode()
            except Exception as e:
                print("Error in communication with client ", e)
            return api_2(conn)
            
        elif data == "16":
            try:
                conn.send(b"Exiting")
                conn.close()
            except Exception as e:
                print("Error in communication with client ", e)
            return
        else:
            try:
                conn.send(b"Invalid option. Try again.\n")
                conn.recv(1024).decode()
            except Exception as e:
                print("Error in communication with client ", e)

def handle_client(conn):
    """Starts with API 1 and transitions based on user choices."""
    api_1(conn)

def server_program():
    host = '0.0.0.0' # listen on all interfaces
    port = 1337     # TODO have to confirm port number

    # server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # SOCK_STREAM for tcp. TODO confirm tcp or udp
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # SOCK_STREAM for tcp. TODO confirm tcp or udp
    server_socket.bind((host, port))
    server_socket.listen(10) # TODO confirm how many concurrent connections and add threading    print(f"Server is running on {host}:{port}")
    print("Server is listening on ", host, ": ", port)

    while True:
        try:
            conn, addr = server_socket.accept()
            print("Connected by ", addr)
            print("Type of conn", type(conn))
            handle_client(conn)
        except Exception as e:
            print("Error handling client", e)

if __name__ == "__main__":
    server_program()