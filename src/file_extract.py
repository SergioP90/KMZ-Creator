# Module to extract coordinate lists from files.

import os
import sys
import inspect
import pandas as pd
from colorama import Fore, Style
from src.exceptions import InvalidFileExtensionError, ExtractionError


def get_valid_extensions():
    """
    Get a list of valid file extensions based on available extractor functions.

    Parameters:
        None

    Returns:
        List of valid file extensions (str)
    """
    valid_extensions = []

    for name, obj in globals().items():
        if inspect.isfunction(obj) and name.startswith("extract_") and name != "extract_coordinates":
            valid_extensions.append(name.split("_")[-1])

    return valid_extensions


def extract_coordinates(file_path):
    """
    Extract coordinates from a file based on its extension.

    Parameters:
        file_path (str): Path to the input file

    Returns:
        List of tuples: (name, x, y, utm_tag, [datum])
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    file_extension = file_path.split('.')[-1].lower()
    func_name = f"extract_{file_extension}"  # Find the function name
    
    if func_name not in globals():
        raise InvalidFileExtensionError(file_extension=file_extension, path=file_path, supported_extensions=get_valid_extensions())
    
    try:
        this_module = sys.modules[__name__]
        func = getattr(this_module, func_name)
        return func(file_path)
    except Exception as e:
        raise ExtractionError(original_exception=e)


# SPECIFIC FILE EXTRACTORS

def extract_txt(file_path):  # Expect each pair of coordinates in a new line, separated by a tab or space
    """
    Extract coordinates from a TXT file.
    Each line should have: name x y utm_tag [datum]

    Example lines:
        PointA 500000 4649776 30T
        PointB 400000 4500000 33N ETRS89

    Parameters:
        file_path (str): Path to the TXT file
        
    Returns:
        List of tuples: (name, x, y, utm_tag, [datum])
    """
    print(f"{Fore.YELLOW}Extracting coordinates from TXT file...{Style.RESET_ALL}")
    points = []
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 4:
                try:
                    name = parts[0]
                    x = float(parts[1].replace(',', '.'))
                    y = float(parts[2].replace(',', '.'))
                    utm_tag = parts[3]
                    points.append((name, x, y, utm_tag))

                except Exception as e:
                    print(f"{Fore.RED}Warning: Could not convert line to float coordinates: {line.strip()}{Style.RESET_ALL}")
                    print(f"{Fore.RED}{str(e)}{Style.RESET_ALL}")
                    continue

            elif len(parts) == 5:
                try:
                    name = parts[0]
                    x = float(parts[1].replace(',', '.'))
                    y = float(parts[2].replace(',', '.'))
                    utm_tag = parts[3]
                    datum = parts[4]
                    points.append((name, x, y, utm_tag))

                except Exception as e:
                    print(f"{Fore.RED}Warning: Could not convert line to float coordinates: {line.strip()}{Style.RESET_ALL}")
                    print(f"{Fore.RED}{str(e)}{Style.RESET_ALL}")
                    continue

            else:
                print(f"{Fore.RED}Warning: Invalid line format (expected 4 or 5 columns): {line.strip()}{Style.RESET_ALL}")
                continue
            
    print(f"{Fore.GREEN}Extracted {len(points)} points from TXT file.{Style.RESET_ALL}")
    return points