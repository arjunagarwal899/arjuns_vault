Useful linux commands:

## Communicate between two servers
```bash
iperf -s  # to start a server on one node
iperf -c host_ip  # to connect as a client
```

## Enable tcp connections between two servers
```bash
sudo iptables -A INPUT -p tcp -s ENTER_SUBNET_HERE -j ACCEPT 
```

## Check read/write speeds of all disks on a server
```bash
iostat -m 1
```

## Check read/write speeds of pwd
```bash
sudo fio --numjobs=1 --randrepeat=1 --ioengine=libaio --direct=1 --gtod_reduce=1 --bs=16k --iodepth=32 --size=1G --readwrite=read --group_reporting --name test1
```