# ML GUI

This repository contains a graphical user interface (GUI) for a Convolutional Neural Network (CNN) model designed to recognize voice from the DAPS dataset and classify it into two classes.

### Installation
To install and set up the project, follow these steps:

Clone the repository:
```bash
git clone https://github.com/MykhailoShamrai/ml_gui.git
cd ml_gui
```


Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
````

Install the required packages:
```bash
pip install -r requirements.txt
```

### Usage

Ensure you have the pretrained model's .pth file in the project folder.

Update the self.models_path attribute in the gui.py file to match the filename of your .pth file:
self.models_path = "your_model_filename.pth"

To ensure that model works properly, download best_cnn_modified.pth from Sharepoint that we provided. Load this model to the folder from which program will be run. 

Run the GUI application:
```bash
python gui.py
````

You can load files from DAPS dataset to our program and also voice can be recorded.

