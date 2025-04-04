import socket
import time
import os

CHUNKSIZE = 1024

# raw data acquired from option 13, is decoded adn written into files.
def write_toFiles(fp1, fp2, virtual_address, byte_count):
    val1_prev = 0
    val2_prev = 0
    p = virtual_address
    mod_num = 2
    word_byte = 4
    skip_words = 2
    count1 = 0
    count2 = 0
    cycles1 = 0
    cycles2 = 0

    for offset in range(0, byte_count, mod_num * word_byte):
        val1 = (p[offset] | (p[offset + 1] << 8) | (p[offset + 2] << 16) | (p[offset + 3] << 24)) & 0xffffffff
        val2 = (p[offset + word_byte] | (p[offset + word_byte + 1] << 8) | (p[offset + word_byte + 2] << 16) | (p[offset + word_byte + 3] << 24)) & 0xffffffff

        val1_val = val1 & 0x7fffffff
        val1_bit = (val1 >> 31) & 0x1
        val2_val = val2 & 0x7fffffff
        val2_bit = (val2 >> 31) & 0x1

        if (val1_val != val1_prev) or (val1_val == 0):
            if val1_val < val1_prev:
                cycles1 = cycles1 + 1

            val1_disp = val1_val + (cycles1 * 2147483648)
            val1_bit = (val1 >> 31) & 0x1
            fp1.write("{0},".format(val1_bit))

            fp1.write("{0}\n".format(val1_disp))
            count1 = count1 + 1

        if (val2_val != val2_prev) or (val2_val == 0):
            if val2_val < val2_prev:
                cycles2 = cycles2 + 1

            val2_disp = val2_val + (cycles2 * 2147483648)
            val2_bit = (val2 >> 31) & 0x1
            fp2.write("{0},".format(val2_bit))
            fp2.write("{0}\n".format(val2_disp))
            count2 = count2 + 1

        val1_prev = val1_val
        val2_prev = val2_val
    fp1.write("\n\n")
    fp2.write("\n\n")

    print("Counts Recorded for DDMTD1: {0} \n".format(count1))
    print("Counts Recorded for DDMTD2: {0} \n".format(count2))
    print("Efficiency for DDMTD1: {0} \% \n".format((count1)*100/offset))
    print("Efficiency for DDMTD2: {0} \% \n".format((count2)*100/offset))

# send the sub-directory which contains Flash_Firmware. 
# path to Flash_Firmware must be sent as input
def send_directory(client, sub_d):
    f_n = sub_d.split('/')[-1]
    for path,dirs,files in os.walk(sub_d):
        for file in files:
            filename = os.path.join(path,file)
            filesize = os.path.getsize(filename)
            
            relpath = os.path.relpath(filename)
            # Extract the desired relative path
            if f_n in relpath:
                relpath = relpath.split(f_n, 1)[-1]  # Get everything after base_path

            print('Sending {0}'.format(relpath[1:]))

            with open(filename,'rb') as f:
                try:
                    client.sendall(relpath[1:] + '\n')
                    client.sendall(str(filesize) + '\n')
                except socket.error as e:
                    print("Socket error:", e)

                # Send the file in chunks so large files can be handled.
                while True:
                    data = f.read(CHUNKSIZE)
                    if not data:
                        break
                    try:
                        client.sendall(data)
                    except socket.error as e:
                        print("Socket error:", e)
                        break
    print('Done.')
    client.sendall("No more files" + '\n')

client_socket = None

def client_program():
    host = '192.168.22.73'
    port = 1337             # TODO find out this data

    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # TODO confirm the udp or tcp
    client_socket.connect((host, port))
    # section varibales refers to the different apis.
    section = 1
    while True:
        # Receive menu/options from the server
        message = client_socket.recv(1024).decode()
        print(message)
        
        if message:
            if message[0] == 'F':
                section = 1
            elif message[0] == 'P':
                section = 2
            elif message[0] == 'D':
                section = 3
        # Get user input and send it to the server
        print("Enter choice: ")
        user_input = input()

        try:
            user_input = str(user_input)
        except Exception as e:
            user_input = "100"

        client_socket.send(str(user_input))

        # send the Flash_Firmware sub-directory to server
        if str(user_input) == "1" and section == 1:

            ptf = client_socket.recv(1024).decode()
            print(ptf)

            path_to_folder = raw_input()

            f_n = path_to_folder.split('/')[-1]
            print(f_n)

            client_socket.send(f_n)
            send_directory(client_socket, path_to_folder)
            response = client_socket.recv(1024).decode()
            print(response)
            client_socket.send(b"Done\n")

        # Send input to server regarding which Firmware to flash to the board
        elif str(user_input) == "3" and section == 1:
            resp = client_socket.recv(1024).decode()
            print(resp)
            choice = raw_input()
            client_socket.send(choice)
            response = client_socket.recv(1024).decode()
            print(response)
            client_socket.send(b"Done\n")

        # enter the configuration files content to be displayed
        # enter 0 if you want to return to main menu
        elif str(user_input) == "9" and section == 2:
            choice = "3"
            while choice != "0":
                resp = client_socket.recv(2048).decode()
                print(resp)
                choice = raw_input()
                client_socket.send(choice.encode())
                resp = client_socket.recv(2048).decode()
                print(resp)
        
            client_socket.send(b"Done\n")

        # select the particular configuration file to be flashed to the board
        elif str(user_input) =="10" and section == 2:
            filepath = client_socket.recv(1024).decode()
            print(filepath)
            opt = raw_input()
            client_socket.send(opt.encode())

            # enter 0 to upload a new configuration file
            if opt == "0":
                print("Enter the filepath")
                fp = raw_input()
                filesize = os.path.getsize(fp)

                client_socket.send(str(fp).encode() + b" " + str(filesize).encode())

                with open(fp,'rb') as f:
                    # Send the file in chunks so large files can be handled.
                    while True:
                        data = f.read(CHUNKSIZE)
                        if not data:
                            break
                        try:
                            client_socket.send(data)
                        except socket.error as e:
                            print("Socket error:", e)
                            break
                
            response = client_socket.recv(1024).encode()
            client_socket.send(b"Done\n")
            print(response)
            
        # recieves the raw data file 
        elif str(user_input) == "13" and section == 3:
            file_data = bytearray()
            length = client_socket.recv(1024).strip()
            length = int(length.decode())
            cp_len = length
            while length:
                chunk = min(length,CHUNKSIZE)
                data = client_socket.recv(chunk)
                if not data: break
                length -= len(data)
                file_data.extend(data)

            fn1 = "./data/ddmtd1.txt"
            fn2 = "./data/ddmtd2.txt"

            dir_path = os.path.dirname(fn1)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

            # wrute theta with open fn1 fn2, as fp1 and fp2
            with open(fn1, 'w') as fp1, open(fn2, 'w') as fp2:
                write_toFiles(fp1, fp2, file_data, cp_len)

            client_socket.send(b"Recieved data\n")
            response = client_socket.recv(1024).encode()
            print(response)
            client_socket.send(b"Done\n")

        # recieves the calculated phase difference
        elif str(user_input) == "14" and section == 3:
            print("Enter the number of iterations")
            no_t_r = input()
            print("Do you want to save the output in output.txt file?(Y/N) ")
            osf = raw_input()
            osf = osf.upper()
            client_socket.send(str(no_t_r).encode())
            dest = "./output.txt"
            # if you enter y or yes or Y, the data will be stored in a output.txt file
            if osf[0] == "Y":
                with open("output.txt", "w") as f:
                    pass

            for i in range(int(no_t_r)):
                ans = ""
                ans = client_socket.recv(1024).decode()
                print(ans)
                if "Failed" in ans:
                    break
                if osf[0] == "Y":
                    f = open("output.txt", "a")
                    f.write(ans)
                    f.close()

            # end new c
            client_socket.send(b"Done\n")

        # ends the connection with the server
        elif str(user_input) == "16" and section == 3:
            response = client_socket.recv(1024).decode()
            print(response)
            break

        else:
            response = client_socket.recv(1024).decode()
            client_socket.send(b"Done\n")
            print(response)

    client_socket.close()

if __name__ == "__main__":
    client_program()