import os
import time
import subprocess

def check_service_health(service_name):
    try:
        # Check if the service is running
        status = subprocess.check_output(['systemctl', 'is-active', service_name]).decode('utf-8').strip()
        return status == 'active'
    except subprocess.CalledProcessError:
        return False

def restart_service(service_name):
    print(f"Restarting {service_name}...")
    subprocess.call(['systemctl', 'restart', service_name])

if __name__ == '__main__':
    SERVICE_NAME = 'your_service_name_here'
    CHECK_INTERVAL = 60  # seconds

    while True:
        if not check_service_health(SERVICE_NAME):
            restart_service(SERVICE_NAME)
        time.sleep(CHECK_INTERVAL)