The main file for GUI is gui.py. To run an app You should firstly run 
from terminal in project folder to install all required packages into virtual environment.
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
After installation You can run an app after choosing "gui" as target.

It's important to add .pth file from ours pretrained model. After changing self.models_path to name
of Your current filename for .pth file in projects folde, everything should work.
