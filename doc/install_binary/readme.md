# Install binary packages

## Install dependencies

Setup your computer to accept software from <http://packages.ros.org>:

```console
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
```

Setup keys:

```console
sudo apt-key adv --keyserver hkp://ha.pool.sks-keyservers.net:80 --recv-key 0xB01FA116
```

Install the necessary packages:

```console
sudo apt update
sudo apt install ros-kinetic-gazebo-ros ros-kinetic-mavros ros-kinetic-opencv3 ros-kinetic-rqt ros-kinetic-xacro
```

## Install uctf package

Setup your computer to accept software from <http://packages.osrfoundation.org>:

```console
sudo sh -c 'echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable `lsb_release -cs` main" > /etc/apt/sources.list.d/gazebo-stable.list'
```

Setup keys:

```console
wget http://packages.osrfoundation.org/gazebo.key -O - | sudo apt-key add -
```

Install the `uctf` package provided from <http://packages.osrfoundation.org>:

```console
sudo apt update
sudo apt install uctf
```

---

Next: [Run an example](../run_example/readme.md).