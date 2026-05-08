import plotly.graph_objects as go
import kaleido
import sys
import os

print(f"Python version: {sys.version}")
print(f"Kaleido version: {kaleido.__version__}")
print(f"Kaleido path: {kaleido.__file__}")

fig = go.Figure(data=[go.Bar(y=[2, 1, 3])])
try:
    img_bytes = fig.to_image(format="png")
    print("Success: Kaleido is working correctly!")
except Exception as e:
    print(f"Error: Kaleido failed to generate image. {e}")
