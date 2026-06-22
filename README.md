# Network Port Scanner GUI 🚀  

A high-performance, multithreaded network port scanner featuring a vibrant, cyberpunk-themed Graphical User Interface (GUI). Built with Python and Tkinter, this tool allows users to quickly scan a target IP address or hostname across a customizable range of ports to identify open connections and their associated services.  

## ✨ Features  

* **High-Speed Concurrency:** Utilizes Python's `threading` module with a semaphore limit (up to 500 concurrent workers) to perform rapid, non-blocking scans.  
* **Interactive Cyberpunk GUI:** Features a dark neon color palette, real-time progress bars, and an active elapsed time tracker.  
* **Smart Terminal Output:** Displays discovered open ports and services (e.g., SSH, HTTP) with syntax highlighting.  
* **Click-to-Copy:** The output is fully interactive—hover over and click any result to instantly copy it to your clipboard.  
* **Thread-Safe Architecture:** Employs a `queue` system to safely pass data between the background scanning workers and the main GUI thread, ensuring high responsiveness.  
* **Export Functionality:** Save the final list of open ports and services to a `.txt` file for easy logging and analysis.  

## 📸 Screenshot  

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/54c1b5bf-d771-44be-bb5f-f3cf135d24c4" />


## 🛠️ Prerequisites  

* **Python 3.7+**  
* **Tkinter** (Usually included with standard Python installations. If you are on Linux, you might need to install it via your package manager, e.g., `sudo apt-get install python3-tk`).  

## 🚀 Installation & Usage  

1. **Clone the repository:**  
```bash
git clone https://github.com/yourusername/network-port-scanner.git
cd network-port-scanner

```


2. **Run the application:**  
```bash
python networkport.py

```


3. **Using the tool:**
* Enter the target IP address or hostname (e.g., `127.0.0.1` or `scanme.nmap.org`).   
* Define your **Start Port** and **End Port** (e.g., `1` to `1024`).  
* Click **Start Scan** and watch the real-time cyberpunk terminal output!  
* Click on any discovered port in the terminal to copy its details.  
* Click **Save Results** when the scan finishes to export your findings.  
