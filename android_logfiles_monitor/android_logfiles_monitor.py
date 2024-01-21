import subprocess
import sys
import threading
import signal
import time

class LogfilesMonitor:
    def __init__(self, filepaths, ip_address, port_number, serial_name=None, stdout_enable=True, out_logfile_name=None):
        """
        Constructor of the LogfilesMonitor class

        Args:
            filepaths (list): List of file paths to monitor
            ip_address (str): IP address of the device to connect
            port_number (int): Port number of the device to connect
            serial_name (str, optional): Serial name of the device to connect. Defaults to None.
            stdout_enable (bool, optional): Enable stdout. Defaults to True.
            output_file (str, optional): Output file path. Defaults to None.
        """
        self.filepaths_in_target = filepaths
        self.processes = [None for _ in self.filepaths_in_target]
        self.threads = [None for _ in self.filepaths_in_target]
        self.device_ip_port = f"{ip_address}:{port_number}"
        if serial_name is None:
            self.serial_name_option = ""
        else:
            self.serial_name_option = "-s " + serial_name
        self.stdout_enable = stdout_enable
        self.out_logfile = None
        if out_logfile_name is not None:
            self.out_logfile = open(out_logfile_name, "w")

    def adb_connect(self):
        """
        Method to connect to the device via ADB

        Returns:
            bool: True if ADB connection is successful, False otherwise
        """
        # connect to the device
        result = subprocess.run(f"adb {self.serial_name_option} connect {self.device_ip_port}", shell=True)
        if result.returncode != 0:
            print(f"Failed to connect to {self.device_ip_port} ({self.serial_name_option})", file=sys.stderr)
            return False
        # set root permission
        result = subprocess.run(f"adb {self.serial_name_option} root", shell=True)
        if result.returncode != 0:
            print(f"Failed to execute adb root command: adb {self.serial_name_option} root", file=sys.stderr)
            return False
        return True

    def run(self, callback=None):
        """
        Method to execute log monitor
        """
        def logs_monitor_thread_proc(filepath_in_target, idx):
            """
            Method for running log monitor in a thread

            Args:
                filepath_in_target (str): File path to monitor
                idx (int): Index of the thread
            """
            # Create a shell script for log monitoring
            sh_script_for_log_monitoring = f"""
            #!/bin/bash
            target={filepath_in_target}
            while [ ! -f "$target" ]; do
                sleep 1
            done
            tail -f "$target" 2>/dev/null
            """
            # send the shell script to the device and execute it
            process = subprocess.Popen(f"adb {self.serial_name_option} shell sh".split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            self.processes[idx] = process
            process.stdin.write(sh_script_for_log_monitoring)
            process.stdin.close()
            # read the output from the process
            while True:
                line = process.stdout.readline()
                # If the line is empty, the process has finished.
                if not line and process.poll() is not None:
                    return
                # Write the output to the output file.
                if self.out_logfile is not None:
                    self.out_logfile.write(line)
                    self.out_logfile.flush()
                # Call the callback function
                if callback is not None:
                    callback(filepath_in_target, line) 
                # Print the output to the console.
                if self.stdout_enable:
                    print(line.strip())

        for idx, filepath_in_target in enumerate(self.filepaths_in_target):
            # Create a thread for running the process
            thread = threading.Thread(target=logs_monitor_thread_proc, args=(filepath_in_target,idx))
            thread.start()
            self.threads[idx] = thread

        # Check the file size every second. If the file size is smaller than the previous one, restart the process.
        filesizes = [0 for _ in self.filepaths_in_target]
        while True:
            for idx, filepath_in_target in enumerate(self.filepaths_in_target):
                current_filesize = 0
                # get the file size
                result = subprocess.run(f"adb {self.serial_name_option} shell \"ls -la {filepath_in_target} | awk '" + "{print $5}'\"", stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True)
                # if the file exists, get the file size
                if result.returncode == 0 and result.stdout.strip().isdigit():
                    current_filesize = int(result.stdout.strip())
                else:
                    current_filesize = 0
                # if the file size is smaller than the previous one, restart the process
                if current_filesize < filesizes[idx]:
                    filesizes[idx] = 0
                    self.processes[idx].kill()
                    self.processes[idx] = None
                    self.threads[idx].join()
                    self.threads[idx] = None
                    thread = threading.Thread(target=logs_monitor_thread_proc, args=(filepath_in_target,idx))
                    thread.start()
                    self.threads[idx] = thread
                else:
                    filesizes[idx] = current_filesize
            time.sleep(1)

    def terminate(self):
        """
        Method to terminate log monitor
        """
        print("terminating!", file=sys.stderr)
        for idx, process in enumerate(self.processes):
            if self.processes[idx] is not None:
                self.processes[idx].terminate()
                self.processes[idx] = None
        for idx, thread in enumerate(self.threads):
            if self.threads[idx] is not None:
                self.threads[idx].join(3)
                self.threads[idx] = None
        if self.out_logfile is not None:
            self.out_logfile.close()
            self.out_logfile = None
        print("terminated!", file=sys.stderr)

def main():
    """
    Main function that monitors log files in real-time from Android devices.
    This function connects to an Android device using ADB, monitors log files specified in `file_lists`,
    """
    # list of log files to monitor
    file_lists = [
        "/mnt/media_rw/tmp/sample.000.log",
        "/mnt/media_rw/tmp/sample.001.log",
        "/mnt/media_rw/tmp/sample.002.log",
        "/mnt/media_rw/tmp/sample.003.log",
        "/mnt/media_rw/tmp/sample.004.log",
    ]
    # create an instance of the LogfilesMonitor class
    log_monitor = LogfilesMonitor(filepaths = file_lists, ip_address = "localhost", port_number = 5555, serial_name = "emulator-5556", out_logfile_name = "sample.log")
    # create a signal handler
    def create_signal_handler():
        def signal_handler(sig, frame):
            log_monitor.terminate()
            sys.exit(0)
        return signal_handler
    # set the signal handler
    signal.signal(signal.SIGINT, create_signal_handler())
    # connect to the devicex
    if not log_monitor.adb_connect():
        sys.exit(1)
    # run log monitoring
    log_monitor.run()
    print("Finished", file=sys.stderr)

if __name__ == "__main__":
    main()