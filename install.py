import os
import subprocess

def install_thc_hydra():
    print("Updating package lists and installing dependencies...")
    subprocess.run(["sudo", "apt-get", "update"], check=True)
    dependencies = [
        "git", "build-essential", "libssl-dev", "libssh-dev", "libidn11-dev",
        "libpcre3-dev", "libgtk2.0-dev", "libmysqlclient-dev", "libpq-dev",
        "libsvn-dev", "firebird-dev", "libncurses5-dev"
    ]
    subprocess.run(["sudo", "apt-get", "install", "-y"] + dependencies, check=True)

    print("Cloning the THC-Hydra repository...")
    subprocess.run(["git", "clone", "https://github.com/vanhauser-thc/thc-hydra.git"], check=True)
    os.chdir("thc-hydra")

    print("Configuring, building, and installing THC-Hydra...")
    subprocess.run(["./configure"], check=True)
    subprocess.run(["make"], check=True)
    subprocess.run(["sudo", "make", "install"], check=True)

    print("THC-Hydra has been successfully installed!")

if __name__ == "__main__":
    try:
        install_thc_hydra()
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during installation: {e}")
