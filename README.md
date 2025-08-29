# SMap6

SMap6 is a 3D space mapping-based IPv6 target generation system for Internet-wide scanning. SMap6 hierarchically maps 128-bit IPv6 addresses into a three-dimensional coordinate space. Subsequently, it utilizes the grid-based neighborhood merging clustering algorithm to identify high-density active regions for address pattern mining. Finally, it generates high-quality target addresses similar to seed addresses based on the hierarchical Hamming distance constraint strategy.

### Dependencies and installation

SMap6 is compateible with Python3.x. You can install the requirements for your version. Besides, RDET uses the following packages:

* argparse

```
pip3 install argparse
```

### zmapv6 installation (ask in IPv4 network)

####  Building from Source

```
git clone https://github.com/tumi8/zmap.git
cd zmap
```

#### Installing ZMap Dependencies

On Debian-based systems (including Ubuntu):

```
sudo apt-get install build-essential cmake libgmp3-dev gengetopt libpcap-dev flex byacc libjson-c-dev pkg-config libunistring-dev
```

On RHEL- and Fedora-based systems (including CentOS):

```
sudo yum install cmake gmp-devel gengetopt libpcap-devel flex byacc json-c-devel libunistring-devel
```

On macOS systems (using Homebrew):

```
brew install pkg-config cmake gmp gengetopt json-c byacc libdnet libunistring
```

#### Building and Installing ZMap

```
cmake .
make -j4
sudo make install
```

### Usage

Parameter meaning introduction：

* budget: type=int,the upperbound of scan times
* input_file:  type=str, input IPv6 addresses
* output_target: type=str,output directory for generated target addresses
* output_Zmap: type=str,Zmap-scanned active addresses output directory
* source_ip: type=str,local IPv6 address
* scan_rate: type=int,number of probe packets sent per second

## Example

```
sudo python3 main.py
```

