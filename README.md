# Water Flow Simulation Editor

> A water flow simulation editing and VR visualization system based on ArUco Marker tracking and Meta Quest 3

![Python](https://img.shields.io/badge/Python-3.9-blue?logo=python)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green?logo=qt)
![Unity](https://img.shields.io/badge/Unity-2022.3.41f1-black?logo=unity)
![Platform](https://img.shields.io/badge/Platform-Meta_Quest_3-purple?logo=meta)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🏆 Accepted to SIGGRAPH 2025 (Poster)
Authors' implementation of the paper <strong>Exploring Real-Time Water Surface Simulation for Immersive Virtual Reality Using Marker-Based Tracking</strong> [**[ Read the Paper]**](https://dl.acm.org/doi/full/10.1145/3721250.3742995)

## 📖 About the Project
This project presents a real-time water flow simulation editing system that integrates **Computer Vision** and **Virtual Reality**. The system consists of two core modules: an editing tool developed in `Python` (`PyQt5`) and a VR visualization client built on the `Unity` engine. The editing tool dynamically generates a `Flowmap` by detecting physical `ArUco Markers`. Then, using the `TCP/IP Socket` protocol, it transmits the Flowmap to the `Meta Quest 3` device for rendering, enabling real-time water flow simulation within the virtual environment.

## ✨ Project Features

This system utilizes a **Server-Client architecture** to bridge the Python-based Editor and Unity-based VR Visualization.

* **Pool Shape Selection**
  Supports both `circular` and `rectangular` pool geometries. The selection dynamically adapts the underlying algorithm logic for accurate simulation.
  ![Pool Selection Demo](Doc/Stage1.gif)

* **Perspective Transform Reference Point Editing**
  Provides an interactive interface to define 4 reference points, calculating the `Perspective Transformation Matrix`. This converts camera feeds into a top-down view to optimize `ArUco Marker` tracking accuracy.
  ![Reference Point Editing Demo](Doc/Stage2.gif)

* **Water Jet Vector Editing**
  Allows intuitive mouse-based control to define the pump position, jet direction, and flow reach. This enables the real-time generation of the `Flowmap` based on physical marker interactions.
  ![Water Jet Vector Editing Demo](Doc/FinalStage.gif)

* **Real-Time Data Transmission**
  Operates over a `TCP/IP` connection where the Editor (Server) transmits the generated `Flowmap` to the VR headset (Client) instantly upon request.

* **VR Visualization on Meta Quest 3**
  Features a high-fidelity water simulation scene built with `Unity Shader Graph`. The client continuously updates the `Flowmap Texture` to render dynamic water flow changes in the virtual environment.

## 📂 Project Structure

The repository is organized into two main directories: `WaterEdit` (Python Editor) and `UnityWaterSimulation` (VR Project).

```text
WaterSimulation/
├── WaterEdit/                           # Python-based Editor Tool (Server Side)
│   ├── UI_Image/                        # Contains PNG icons used in the user interface
│   ├── ArUco_to_FlowMap.py              # Main Script. Handles ArUco tracking, Flowmap generation, and UI logic
│   ├── ArUcoFlowMap_UI.py               # Defines the PyQt5 UI layout and widget configuration
│   ├── TCP_Server.py                    # Implements TCP/IP protocol logic for data transmission
│   └── requirements.txt                 # List of required Python libraries
│
└── UnityWaterSimulation/                # Unity VR Project (Client Side)
    └── Assets/
        ├── WaterSimulationScene/
        │   └── WaterDemo.unity          # The main scene for VR visualization
        ├── Waterflow_Shader/            # Shader Graph resources for fluid rendering
        │   ├── Flow.mat                 # Water surface material instance
        │   ├── PT_FlowMap.shadergraph   # Main Shader Graph logic for the water effect
        │   └── USG_FlowMap 1.shadersubgraph
        └── ServerConnectionScript/
            └── FlowmapUpdateClient.cs   # Client script. Requests and updates the Flowmap texture via TCP
```

## 🚀 Getting Started

### Installation
First, clone repository using the "Code" button above or or using the following command:
```sh
git clone https://github.com/Li-En-Lai/WaterSimulation.git
```
### 1. Setup Editor Tool (Server Side)
This project uses **Conda** to manage the Python environment.

* Create a Conda virtual environment named `water_edit` with Python 3.9:
    ```bash
    conda create -n water_edit python=3.9
    ```
* Activate the virtual environment:
    ```bash
    conda activate water_edit
    ```
* Navigate to the `WaterEditTool` folder and install the required libraries:
    ```bash
    pip install -r requirements.txt
    ```
### 2. VR Visualization Unity Project (Client Side)
To open the project,you need **UnityHub**
* Open Unity Hub.
* Click the "Add" button and select "Add project from disk".
* Navigate to the cloned repository folder and select the `UnityWaterSimulation` folder to add it to Unity Hub.
* Once added, click on `UnityWaterSimulation` in the **Project List** to open the project.

## 📋 Usage

### 1. Editor Tool (Server Side) 🖥️
* **Navigate to the directory:**
   Enter the editor project folder.
   ```bash
   cd WaterEditTool
   ```
* **Activate Virtual Environment:** Ensure the water_edit environment is created and activated.
    ```bash
    conda activate water_edit
    ```
* **Run the Application:** Execute the main script in the terminal. The Server will start automatically.
    ```bash
    python ArUco_to_FlowMap.py
    ```
    **Note:** Once the editing process is complete, the Server will stand by. It will continuously transmit the generated Flowmap upon receiving a request from the Client.

### 2. VR Visualization (Client Side) 🥽
**Step 1: Network Configuration in Unity**

* Open the project and locate the ```FlowMapClient``` object in the ```Hierarchy window```. (This object handles data reception and updates the water surface texture.)

* Select the object and find the settings in the        ```Inspector window```.

* Modify the ```Server IP``` to match your computer's IPv4 address.
(**Tip:** You can check your IP by typing the following command in CMD)
    ```bash
    ipconfig
    ```
* The ```Server Port``` can also be adjusted (**Default is** ```8888```).

**Step 2: Build & Deploy**

* Build the project as an **APK**.
* Import/Install the APK into your **Meta Quest 3**.

**Step 3: VR Interaction**

* Ensure the **Server (Editor Tool)** is already running.
* Launch the ```WaterSimulation app``` on Quest 3. It will automatically connect to the Server.
* Use the **Right Hand Controller** to control the transmission:
    * Press ```A``` Button: Request the Server to **start transmitting** the generated ```Flowmap```.
    * Press ```B``` Button: Request the Server to **stop transmission**.

## 🎓 Citation

If you find this project useful for your research, please cite our poster:
```bibtex
@inproceedings{lai2025exploring,
  title={Exploring Real-Time Water Surface Simulation for Immersive Virtual Reality Using Marker-Based Tracking},
  author={Lai, Li-En and Lin, Chi-Yu and Pan, Tse-Yu and Han, Ping-Hsuan},
  booktitle={Proceedings of the Special Interest Group on Computer Graphics and Interactive Techniques Conference Posters},
  pages={1--2},
  year={2025}
}
```