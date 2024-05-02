## Install requirements 

```bash
python -m venv virtualenvs/manim
source virtualenvs/manim/bin/python
pip install -r requirements.txt
```

## Build an animation

```bash
manim -pql result.py     # low quality video
manim -p result.py       # high quality video
manim -pql -s result.py  # low quality last frame only (img)
```
