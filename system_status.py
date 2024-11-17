# Options for gettin stats like cpu, ram and storage usage

import psutil
import os
import platform
import multiprocessing
import GPUtil


################## psutil ####################

# CPU usage
cpu_percent = psutil.cpu_percent(interval=1)  # Percentage over 1 second
cpu_count = psutil.cpu_count(logical=True)  # Number of logical CPUs

# Memory usage
memory = psutil.virtual_memory()
total_memory = memory.total
available_memory = memory.available
used_memory_percent = memory.percent

# Disk usage
disk = psutil.disk_usage('/')
total_disk = disk.total
used_disk = disk.used
free_disk = disk.free
used_disk_percent = disk.percent

################## os ####################

# Disk space
statvfs = os.statvfs('/')
total_disk = statvfs.f_frsize * statvfs.f_blocks  # Total space
free_disk = statvfs.f_frsize * statvfs.f_bfree    # Free space

################## platform and multiprocessing ####################

cpu_count = multiprocessing.cpu_count()
os_name = platform.system()
architecture = platform.architecture()

################## GPUtil ####################

gpus = GPUtil.getGPUs()
for gpu in gpus:
    print(f"GPU id: {gpu.id}, GPU usage: {gpu.load * 100}%, Memory usage: {gpu.memoryUtil * 100}%")