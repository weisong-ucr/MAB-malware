# MAB-Malware

This project is the implementation of the paper: [MAB-Malware: A Reinforcement Learning Framework for Attacking Static Malware Classifiers](https://arxiv.org/abs/2003.03100).

![GitHub Logo](/workflow.png)

MAB-Malware an open-source reinforcement learning framework to generate AEs for PE malware. We model this problem as a classic multi-armed bandit (MAB) problem, by treating each action-content pair as an independent slot machine. We model each machine's reward as a Beta distribution and use Thompson sampling to select the next action and content, striking a balance between exploitation and exploration. We devise an action minimization process, which minimizes an AE by removing redundant actions and further reducing essential actions into even smaller actions (called micro-actions). We then assign rewards only to these essential micro-actions. This minimization process also helps interpret the root cause of evasions.

# How to use

## Directly use our docker image. (Recommended)

```sh
$ sudo apt install docker.io
$ sudo docker pull wsong008/mab-malware
$ sudo docker run -ti wsong008/mab-malware bash
```

### Run the adversarial attacks on EMBER.

In the docker container, run:

```sh
$ python run_attack.py
```

After the attack, the evasive samples are in the folder: output/evasive/, the minimized evasive samples are in the folder: output/minimal/.

By default, the framework attacks 1000 samples under the folder data/malware/. You can attack your own dataset by mounting your folder to the docker.

```sh
$ sudo docker run -ti -v [malware_folder_path_on_host_OS]:/root/MAB-malware/data/malware wsong008/mab-malware bash
```

### Run the adversarial attack on MalConv.

In the same docker container, modify conf/configure.ini by changing the CLASSIFIER name from 'ember' to 'malconv', and run:

```sh
$ python run_attack.py
```

### Run the adversarial attacks on AV engines.

a) Preparation for the guest machine.

- Install VirtualBox:

```sh
$ sudo apt install virtualbox
```

- Create a virtual machine in VirtualBox. Install the antivirus software you want to evaluate.

- In VirtualBox, Click File -> Host Network Manager, create a network "vboxnet0" if not exists.

- Select your virtual machine, press Ctrl + S to start the "Settings" window. Select "Network", change "Attached to" to "Host-only Adapter".

- Create a shared folder: Create a folder named "share" on the Desktop folder of the guest machine. Right-click the folder and click "Properties". Open the "sharing" tab and click "Advanced Sharing". Check the "share this folder" box and click on "Permissions". Choose "everyone" to give full control. Open the "Security" tab and click Edit. Select "Everyone" in the "Group or user names" to give full control. If "Everyone" does not exist, click on "Add" to create one.
  
- Set a static IP address for the guest machine. For example, 192.168.56.56.

- Start the guest virtual machine.

b) Mount a share folder to the guest machine.

```sh
$ mkdir /home/[username of host OS]/share
$ sudo apt-get install cifs-utils
$ sudo mount -t cifs -o username=[username of guest OS],domain=MYDOMAIN,uid=1000 //192.168.56.56/share/ /home/[username of host OS]/share/
```

c) Run the docker.

```sh
$ sudo docker run -ti -v /home/[username of host OS]/share:/root/MAB-malware/data/share wsong008/mab-malware bash
```

In the docker container, modify conf/configure.ini by changing the CLASSIFIER name from 'ember' to 'av', then run:

```sh
$ python run_attack.py
```
