# Welcome to *apex*™! 🚀

## Project Overview
*apex* is a system that enables LLM-powered agents to act as the primary interface between the user and system, enabling advanced AI collaboration for any task. It represents a new way to interact with one's PC; simply engage in a conversation as one would a colleague and get work done. Actions will be performed automatically to accomplish tasks a user collaboratively specifies alongside the tool. It also connects to a hosted memory of prior experiences, which allows *apex* to learn from previous experiences. 

In a way, *apex* gives LLMs a 'body' in the form of the machine the software is running on. *apex* utilizes a combination of cutting-edge techniques, including Tree of Thought, RAG, dynamic vector-store memory, multi-agent collaboration, and most importantly, a tool-free architecture, to deliver an experience designed for robust performance in the long term. 

__This architecture is built for the future. It is not constrained by fixed tools, and leverages LLM-powered soft reasoning wherever possible. *This means that while it may stumble a bit now*, as the experience pool grows, the codebase matures, and LLMs become more powerful, this tool will become increasingly generally capable.__ 🌱

## Why this matters 🌟

Human-computer interaction has changed dramatically over the history of computer science. From plugboards, to switches, to punch cards, to interactive terminals, and now the mouse and GUI, we have progressively abstracted ourselves away from the truth of the machine so we can be more productive. 

__LLM-powered agents are the frontier of practical AI, but most attempts do not capture the state of the art.__ This is because they are focused on high performance in the short term; they provide LLMs with hardcoded tools along with corresponding use instructions for narrowly defined task scopes. This facilitates reliable performance but narrows capability and is incapable of growth. __By harnessing the cutting edge in research and employing novel techniques, apex™ takes a step beyond what is currently available to the public and aims to enhance user productivity is ways current approaches are incapable of.__

## Installation Instructions

### Windows
1. __Install Python__
    1. Download the __Python 3.10.11__ installer for your architecture at https://www.python.org/downloads/release/python-31011/
    2. Run the installer
        - Ensure ```Add python.exe to PATH``` is checked
        - Check ```Use admin priviliges when installing py.exe``` according to your preference
            - If you're the only user on your personal machine, checking this box can make Python usage more convenient. However, in a managed environment or if you prefer keeping installations user-specific, you might choose to leave it unchecked.
    3. Choose ```Install Now```
    4. Choose ```Disable path length limit``` when prompted
    5. Close the installer
2. __Ensure Python command is recognized__
    1. Open the Start menu
    2. Type ```environment variables```
    3. Choose ```Edit the system environment variables```
    4. Click the ```Environment Variables...``` button under the ```Advanced``` tab
    5. Select ```Path``` under ```User variables for <your_username>``` and choose ```Edit...```
    6. Ensure ```C:\Users\rod_j_m\AppData\Local\Programs\Python\Python310\Scripts\``` and ```C:\Users\rod_j_m\AppData\Local\Programs\Python\Python310\``` are listed __above__ ```%USERPROFILE%\AppData\Local\Microsoft\WindowsApps``` by using the ```Move Up``` and ```Move Down`` buttons
3. __Clone the repo__
    1. Install ```git``` if not already installed
        1. Navigate to https://gitforwindows.org/
        2. Click ```Download```
        3. Run the installer executible
            - You may uncheck ```Windows Explorer integration``` depending on preference
            - We reccommend ```Nano``` as the preferred editor for first-time users
            - Other options may be safely left as default
        4. Continue through the installation
    2. Open ```File Explorer``` and navigate to your preferred installation direftory for *apex*
    3. Right-click and select ```Open in Terminal```
    4. Run ```git clone https://github.com/AgentAITechnologies/apex.git```
4. __Configure the program__
    1. Using the same terminal, change directory into the *apex* folder by running ```cd apex```
    2. Run ```.\win_install.ps1```
        - Enter your Anthropic API key when prompted (See https://docs.anthropic.com/en/docs/initial-setup for guidance on managing Anthropic API keys)
5. __Run the program__
    1. In the *apex* folder, right-click and open Terminal
    1. Run ```.\win_run.ps1```

### Linux
⏳ Deatiled instructions coming soon!

## Tips 💡
We encourage you to push *apex* to the limits of its capability, and even a little beyond what you think it can handle.

*apex* learns from prior experience and human feedback. By allowing *apex* to develop a diverse experience pool with salient feedback, its performance will increase over time. We encourage you to allow full telemetry so *apex* may learn from your interactions *(you will have the opportunity to review any and all information sent to us)*.

That being said, this product is in an *experimental* stage of development. Do not expect it to be able to reliably complete tasks involving high levels of complexity or scale at this time (we do expect it to be capable of such tasks with further feature implementations and a broad experience pool).

__*apex* is best suited for tasks that directly map onto programmatic interaction with the computer (such as Python or shell scripts) than tasks that require mouse and keyboard emulation or visual screen interpretation. This tool is currently better equipped to, say, compile a list of machines on a network vulnerable to some new exploit and automatically patch them than to research especially fluffy cat breeds online.__

## Heads up 🚨
*apex* may not always complete a task the way you want it the first time. In fact, at this time, it will probably fail more than it succeeds. This is expected at this stage, as the experience pool is incredibly small, and many important features are not yet implemented. By enabling telemetry and providing high-quality feedback, expect performance on tasks related to the ones you have tried to increase over time (it takes a little while for new experiences to be ingested by our memory backend).


---

__Thank you for your interest in our project!__ 🙏
