from pathlib import Path
from datetime import datetime, timedelta
from dateutil.parser import parse
import numpy as np
from pandas import read_csv
from xarray import DataArray


def read_mgs_occultation(imgfn):
    imgfn = Path(imgfn).expanduser()

    lblfn = imgfn.with_suffix(".lbl")
    srtfn = imgfn.with_suffix(".srt")

    P = read_mgs_lbl(lblfn)
    nSamp = int(P.at["LINE_SAMPLES", 1])
    nLine = int(P.at["LINES", 1])
    scale = float(P.at["SCALING_FACTOR", 1])
    offs = float(P.at["OFFSET", 1])

    data = np.fliplr(
        (np.fromfile(str(imgfn), dtype="int16", count=nSamp * nLine).newbyteorder("B") * scale + offs).reshape(
            nSamp, nLine, order="F"
        )
    )
    # %% freq
    fs = 4.88  # step [Hz], from .lbl description
    f0 = 0  # Hz
    fend = 2500  # Hz
    f = np.arange(f0, fend - fs, fs)
    # %% time
    t = get_occult_time(srtfn)

    df = DataArray(data=data.T, dims=["time", "freq"], coords={"time": t, "freq": f})

    return df


def read_mgs_lbl(fn):
    # %% parse the very messy .lbl file to get binary .sri file parameters
    """
    this is extremely messy in Matlab, can crash Matlab, and doesn't work in Octave.
    hence a move to Python. Much faster to write and understand.
    """

    fn = Path(fn).expanduser()
    lbl = read_csv(fn, sep="=", index_col=0, header=None)
    lbl.index = lbl.index.str.strip()
    return lbl


def get_occult_time(srtfn: Path):
    srtfn = Path(srtfn).expanduser()
    # %% get epoch date
    t0 = parse(srtfn.read_text().split(",")[0])
    epoch = datetime(t0.year, t0.month, t0.day)
    # %% get all times
    texp = np.loadtxt(srtfn, skiprows=1, usecols=[0], delimiter=",")

    return epoch + np.array([timedelta(seconds=s) for s in texp])
