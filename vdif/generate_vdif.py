import numpy as np
from baseband import vdif
import astropy.units as u
from astropy.time import Time
import argparse
from datetime import datetime


def generate_random_array(size, values, probabilities):
    """
    Generate a random array of a specified size with values drawn from a given set
    according to specified probabilities.

    Parameters:
    - size (int): The size of the random array to generate.
    - values (list): The set of values to choose from.
    - probabilities (list): The probabilities associated with each value in 'values'.

    Returns:
    - np.ndarray: An array of random values.
    """
    # Ensure probabilities sum to 1
    probabilities = np.array(probabilities)
    probabilities /= probabilities.sum()

    # Generate the random array
    random_array = np.random.choice(values, size=size, p=probabilities)
    return random_array


def generate_vdif(filename, sample_rate, num_samples, num_threads, time=None):
    """
    Generate a VDIF file with random data.

    Parameters:
    - filename (str): The output VDIF file name.
    - sample_rate (int): The output VDIF sample rate in Hz.
    - num_samples (int): The number of samples to write.
    - num_threads (int): The number of threads in the VDIF file.
    - time (str or Time, optional): The time for the VDIF file. Defaults to the current time.

    Returns:
    - None
    """
    values = np.asarray([-3.316505, -1., 1., 3.316505])
    probabilities = (1/6) * np.asarray([1, 2, 2, 1])

    if time is None:
        time = Time.now()
    elif isinstance(time, str):
        time = Time(time)

    # Standard vdif sizes are 1032 and 5032 bytes per frame
    with vdif.open(
        filename, 'ws', sample_rate=sample_rate * u.Hz,
        samples_per_frame=4000, nchan=1, nthread=num_threads,
        complex_data=False, bps=2, edv=3, station=65532,
        time=time
    ) as fw:
        fw.write(generate_random_array(
            size=(num_samples, num_threads),
            values=values,
            probabilities=probabilities
        ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a sample VDIF file.")
    parser.add_argument("filename", type=str, help="Output VDIF file name")
    parser.add_argument("sample_rate", type=int, help="Output VDIF Sample Rate (Hz)")
    parser.add_argument("num_samples", type=int, help="Number of samples to write")
    parser.add_argument("num_threads", type=int, help="Number of threads in VDIF file")
    parser.add_argument(
        "--time", type=str, help="Time for the VDIF file (in ISO format, e.g., '2024-06-16T05:56:07.000000000'). "
                                 "If not provided, the current time will be used."
    )

    args = parser.parse_args()
    generate_vdif(
        args.filename, args.sample_rate, args.num_samples, args.num_threads,
        time=args.time if args.time else None
    )
