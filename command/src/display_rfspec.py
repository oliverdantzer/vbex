import paramiko
import os
import time
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as anim
from collections import deque
import threading
import queue
import sys

# Configuration
SAGGITARIUS_IP = '192.168.2.2'
SAGGITARIUS_USER = 'saggitarius'
SAGGITARIUS_PASSWORD = 'three_little_pigs!'
REMOTE_DATA_PATH = '/media/saggitarius/T7'

# Data buffering
MAX_POWER_SAMPLES = 1000  # Maximum number of power samples to store
MAX_SPECTRUM_SAMPLES = 10  # Number of spectrum samples to read at once
DISPLAY_WINDOW = 20  # Display window in seconds (shortened for faster rates)
UPDATE_INTERVAL = 50  # Animation update interval in ms (faster updates)

# Thread-safe queues for data exchange
spectrum_queue = queue.Queue(maxsize=100)
power_queue = queue.Queue(maxsize=1000)
stop_event = threading.Event()

last_read_position = 0  # Track file position for efficient reading


def read_file_from_position(sftp, file_path, position, max_lines=None):
    """Read file from the given position and update the position."""
    global last_read_position
    
    try:
        with sftp.open(file_path, 'r') as f:
            f.seek(position)
            lines = []
            line_count = 0
            
            while True:
                line = f.readline()
                if not line:
                    break
                    
                lines.append(line)
                line_count += 1
                
                if max_lines and line_count >= max_lines:
                    break
            
            last_read_position = f.tell()
            return lines, last_read_position
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return [], position

def parse_spectrum_data(lines):
    results = []
    for line in lines:
        try:
            parts = line.strip().split()
            if len(parts) < 2049:  # Timestamp + 2048 spectrum values
                print(f"Invalid spectrum data: {line[:50]}...")
                continue
                
            timestamp = float(parts[0])
            spectrum = np.array([float(x) for x in parts[1:2049]])  # Ensure we get exactly 2048 values
            
            # Apply 10*np.log10() to the spectrum data
            spectrum = 10 * np.log10(spectrum + 1e-10)  # Add small value to avoid log(0)
            spectrum = np.flip(spectrum)
            results.append((timestamp, spectrum))
        except Exception as e:
            print(f"Error parsing spectrum line: {e}")
    
    return results


class RfSpecDisplay:
    def __init__(self, selected_folder):
        # Create figure and axes
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle('Saggitarius Spectrometer Data', fontsize=16)
        plt.tight_layout(pad=3.0, rect=[0, 0.03, 1, 0.95])  # Add padding between subplots
        
        # Configure frequency axis for spectrum plot
        fs = 3932.16 / 2
        Nfft = 2**11
        fbins = np.arange(-Nfft // 2, Nfft // 2)
        df = fs / Nfft
        faxis = fbins * df + fs / 2
        faxis = faxis[::-1]
        
        # Initial empty plots
        spectrum_line, = ax1.plot(faxis/1000 + 21, np.zeros(2048), '-', linewidth=1)
        ax1.set_xlabel('Frequency (GHz)')
        ax1.set_ylabel('Power (dB arb.)')
        ax1.set_title('Spectrum')
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Reference start time for relative timestamps
        start_time = None
        
        # Variable to track the latest timestamp for title updates
        latest_timestamp = None
        
        # Create the animation with faster update interval
        ani = anim.FuncAnimation(fig, update, interval=UPDATE_INTERVAL, blit=True)
        
        # Show the plot
        plt.show()
    
    def update(self, filepath):
        nonlocal start_time, latest_timestamp
        
        try:
            spectrum_time, spectrum = latest_spectrum
            latest_timestamp = spectrum_time
            
            # Update current spectrum
            spectrum_line.set_ydata(spectrum)
            
            # Adjust y-axis limits with some padding
            y_min, y_max = spectrum.min(), spectrum.max()
            y_range = y_max - y_min
            ax1.set_ylim([y_min - 0.05*y_range, y_max + 0.05*y_range])
            
            # Update main title with timestamp
            current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(spectrum_time))
            fig.suptitle(f'Saggitarius Spectrometer Data - {current_time_str}', fontsize=16)
                
                    
        except Exception as e:
            print(f"Error updating plot: {e}")
            import traceback
            traceback.print_exc()
        
        return spectrum_line, power_line, avg_power_text
    
    def __del__(self):
        plt.close('all')
