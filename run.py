"""Lanzador: limita los hilos de OpenBLAS/OpenMP ANTES de que Streamlit cargue numpy.
Uso: python run.py   (equivale a streamlit run app.py)"""
import os
import subprocess
import sys

for var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(var, "1")

sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", "app.py", *sys.argv[1:]]))
