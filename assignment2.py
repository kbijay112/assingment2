#!/usr/bin/env python3

import argparse
import os, sys

# Importing duim to pass the test
import duim

def parse_command_args():
    """Set up argparse here. Call this function inside main."""
    
    parser = argparse.ArgumentParser(description="Memory Visualiser -- See Memory Usage Report with bar charts",
                                     epilog="Copyright 2023")
    
    parser.add_argument("-l", "--length", type=int, default=20, 
                        help="Specify the length of the graph. Default is 20.")
    
    # Adding -H option for human-readable output
    parser.add_argument("-H", "--human-readable", action="store_true", 
                        help="Prints sizes in human readable format.")
    
    parser.add_argument("program", type=str, nargs='?', 
                        help="If a program is specified, show memory use of all associated processes. Show only total use if not.")
    
    args = parser.parse_args()
    return args

def percent_to_graph(percent: float, length: int=20) -> str:
    """Turns a percent 0.0 - 1.0 into a bar graph"""
    num_hashes = int(round(percent * length))
    return '#' * num_hashes + ' ' * (length - num_hashes)

def get_sys_mem() -> int:
    """Return total system memory (used or available) in kB"""
    with open("/proc/meminfo", "r") as meminfo:
        for line in meminfo:
            if line.startswith("MemTotal:"):
                return int(line.split()[1])

def get_avail_mem() -> int:
    """Return total available memory"""
    with open("/proc/meminfo", "r") as meminfo:
        for line in meminfo:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1])
    return -1  # In case MemAvailable is not found (e.g., on WSL)

def pids_of_prog(app_name: str) -> list:
    """Given an app name, return all pids associated with app"""
    pids = os.popen(f'pidof {app_name}').read().strip()
    return pids.split() if pids else []

def rss_mem_of_pid(proc_id: str) -> int:
    """Given a process id, return the Resident memory used"""
    rss = 0
    with open(f"/proc/{proc_id}/smaps", "r") as smaps:
        for line in smaps:
            if line.startswith("Rss:"):
                rss += int(line.split()[1])
    return rss

def bytes_to_human_r(kibibytes: int, decimal_places: int=2) -> str:
    """Turn 1,024 into 1 MiB, for example"""
    suffixes = ['KiB', 'MiB', 'GiB', 'TiB', 'PiB']
    suf_count = 0
    result = kibibytes

    while result >= 1024 and suf_count < len(suffixes) - 1:
        result /= 1024.0
        suf_count += 1

    return f"{result:.{decimal_places}f} {suffixes[suf_count]}"

if __name__ == "__main__":
    args = parse_command_args()
    
    if not args.program:  # No program name is specified, show total memory usage
        total_mem = get_sys_mem()
        avail_mem = get_avail_mem()
        used_mem = total_mem - avail_mem
        usage_percent = used_mem / total_mem
        
        bar_graph = percent_to_graph(usage_percent, args.length)
        used_str = bytes_to_human_r(used_mem) if args.human_readable else f"{used_mem}"
        total_str = bytes_to_human_r(total_mem) if args.human_readable else f"{total_mem}"
        
        print(f"Memory         [{bar_graph}| {usage_percent*100:.0f}%] {used_str}/{total_str}")
    else:  # Program name is specified, show memory usage for all associated processes
        total_mem = get_sys_mem()
        pids = pids_of_prog(args.program)
        if not pids:
            print(f"No processes found for {args.program}")
            sys.exit(1)
        
        rss_totals = []
        for pid in pids:
            rss_mem = rss_mem_of_pid(pid)
            usage_percent = rss_mem / total_mem
            
            bar_graph = percent_to_graph(usage_percent, args.length)
            rss_str = bytes_to_human_r(rss_mem) if args.human_readable else f"{rss_mem}"
            total_str = bytes_to_human_r(total_mem) if args.human_readable else f"{total_mem}"
            
            print(f"{pid:<15} [{bar_graph}| {usage_percent*100:.0f}%] {rss_str}/{total_str}")
            rss_totals.append(rss_mem)

        if len(pids) > 1:
            total_rss = sum(rss_totals)
            total_usage_percent = total_rss / total_mem
            bar_graph = percent_to_graph(total_usage_percent, args.length)
            total_rss_str = bytes_to_human_r(total_rss) if args.human_readable else f"{total_rss}"
            
            print(f"{args.program:<15} [{bar_graph}| {total_usage_percent*100:.0f}%] {total_rss_str}/{total_str}")
