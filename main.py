# Create a KMZ from XY coordinates into google earth's coordinate system (WGS84 geographic coordinates (EPSG:4326))

import cmd
import os
import shutil

from colorama import init, Fore, Style

import src.file_extract as fe
import src.transformer as tf
import src.kmz_gen as kg

CONTEXT = {
    "ChangesMade": False,  # Track if changes have been made to the current KMZ
    "Datum": "WGS84",  # Default datum for UTM to lat/lon transformations
    "kmz_manager": None,  # KMZ object we are working with
}

ALIASES = {
    "exit": ["quit", "q", "e", "x", "EOF"],
    "clear": ["cls"],
    "create": ["new", "n", "c"],
    "open": ["load", "l", "o"],
    "save": ["s"],
    "showpoints": ["sp", "points", "listpoints", "lp", "list"],
    "addlonlat": ["addlatlon", "al", "npl", "addclassic", "addll"],
    "addutm": ["au", "autm", "addutm", "np", "add"],
    "addlist": ["addfile", "afl"],
    "setdatum": ["stdt", "setdt"],
    "resetdatum": ["rstd", "resetdt"],
    "datum": ["dt"],
    "status": ["stat", "st"],
    "delete": ["del", "dp", "remove"],
    "modpoint": ["mp", "mpoint", "modp"],
    "distancesall": ["distall", "distanceall", "distall"],
    "distances": ["dist", "distance", "distancesline", "distline"],
    "art": ["asciirt", "ascii"]
}

init(autoreset=True)  # Initialize colorama for windows compatibility


class KMZShell(cmd.Cmd):
    intro = f"\n{Style.BRIGHT}{Fore.CYAN}Welcome to the KMZ Creator. Type help or ? to list commands.\nCopyright Sergio Pozuelo 2025 | Github: https://github.com/SergioP90\n{Fore.YELLOW}WARNING: If when adding a point in UTM format you compare it with a point placed manually in UTM on Google Earth you find that they do not match by <1m, is likely Google Earth has removed the decimal places. Try to generate the kmz without decimals to have them match.{Style.RESET_ALL}"
    prompt = f"\n{Fore.CYAN}[KMZ-CRT] >>>{Style.RESET_ALL} "

    # === OVERRIDES ===
    def default(self, line):
        cmd, *args = line.split()

        # Find which real command this alias maps to
        for real_cmd, aliases in ALIASES.items():
            if cmd == real_cmd or cmd in aliases:
                func = getattr(self, f"do_{real_cmd}", None)
                if func:
                    return func(" ".join(args))
        
        print(f"{Fore.RED}Unknown command: {cmd}{Style.RESET_ALL}")


    def do_help(self, arg):
        if arg:
            # Specific help for one command (with aliases shown)
            cmd_name = self.resolve_alias(arg)
            if cmd_name:
                func = getattr(self, "do_" + cmd_name, None)
                if func and func.__doc__:
                    print(f"{Fore.CYAN}\nHelp for '{Fore.GREEN}{cmd_name}{Fore.CYAN}':{Style.RESET_ALL}")
                    print(f"{Fore.CYAN}{func.__doc__}{Style.RESET_ALL}")
                    aliases = ALIASES.get(cmd_name, [])
                    if aliases:
                        print(f"{Fore.CYAN}Aliases:{Style.RESET_ALL}", ", ".join(aliases))
                else:
                    print(f"{Fore.RED}No help available for {arg}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Unknown command: {arg}{Style.RESET_ALL}")
        else:
            # General help
            print(f"""{Fore.CYAN}\n
Thank you for using KMZ Creator!

Start by creating or opening a KMZ file to work with. This can be done with the {Fore.GREEN}create {Fore.CYAN}or {Fore.GREEN}open <path> {Fore.CYAN}commands.
Use {Fore.GREEN}status {Fore.CYAN}to check if a KMZ is loaded and if there are unsaved changes.

From here, you can begin modifying the KMZ by adding points with {Fore.GREEN}addlonlat{Fore.CYAN}, {Fore.GREEN}addutm{Fore.CYAN}, or {Fore.GREEN}addlist{Fore.CYAN}.

Remember to save your changes with {Fore.GREEN}save <path>{Fore.CYAN} when done.

In this help menu, the available commands are listed with their aliases in parentheses.

{Style.RESET_ALL}""")

            print(f"{Fore.CYAN}\nList of available commands:{Style.RESET_ALL}")

            commands = self.get_commands_with_aliases()

            # Format into columns
            width = shutil.get_terminal_size((80, 20)).columns
            col_width = max(len(c) for c in commands) + 4
            cols = max(1, width // col_width)

            for i, entry in enumerate(commands, 1):
                print(entry.ljust(col_width), end="")
                if i % cols == 0:
                    print()
            if len(commands) % cols != 0:
                print()

            print(f"\n{Fore.CYAN}Type {Fore.GREEN}help <command>{Style.RESET_ALL} {Fore.CYAN}for specific help and descriptions.{Style.RESET_ALL}")


    # === HELPERS ===

    def get_commands_with_aliases(self):
        """Return a list of formatted command+aliases strings."""
        result = []
        seen = set()

        for name in self.get_names():
            if name.startswith("do_"):
                cmd_name = name[3:]
                if cmd_name in seen:
                    continue
                seen.add(cmd_name)

                aliases = ALIASES.get(cmd_name, [cmd_name])
                alias_list = [cmd_name] + aliases
                result.append(
                    Fore.GREEN + cmd_name + Style.RESET_ALL +
                    f" {Fore.YELLOW}(" + ", ".join(alias_list) + f"){Style.RESET_ALL}"
                )

        return sorted(result)


    def resolve_alias(self, name):
        """Return canonical command name for a given alias."""
        if hasattr(self, "do_" + name):
            return name
        for cmd_name, aliases in ALIASES.items():
            if name in aliases or name == cmd_name:
                return cmd_name
        return None


    # === DEFAULT COMMANDS ===

    def do_exit(self, line):
        """
        Exit the KMZ Creator.
        
        Example: 
            exit
        """
        if CONTEXT["ChangesMade"]:
            confirm = input(f"{Fore.YELLOW}You have unsaved changes. Are you sure you want to exit?\nALL UNSAVED CHANGES WILL BE LOST (y/n): {Style.RESET_ALL}")
            if confirm.lower() != 'y':
                print(f"{Fore.YELLOW}Exit cancelled.{Style.RESET_ALL}")
                return False
        print(f"{Fore.RED}Exiting KMZ Creator...{Style.RESET_ALL}")
        return True

    
    def do_clear(self, line):
        """
        Clear the console screen.
        
        Example: 
            clear
        """
        os.system('cls' if os.name == 'nt' else 'clear')
        print(self.intro)


    def do_setdatum(self, line):
        """
        Set the default datum for UTM to lat/lon transformations. If you don't know what this means, just leave it as WGS84.
        You can specify it directly when adding UTM points as well just for that case.

        Usage:
            setdatum DATUM_NAME

        Example:
            setdatum WGS84

        Supported datums: WGS84, NAD83 (American standard), ETRS89 (Spanish standard)
        """
        datum = line.strip()
        if not datum:
            print(f"{Fore.RED}Error: No datum provided. Current datum is {CONTEXT['Datum']}.{Style.RESET_ALL}")
            return
        
        supported_datums = ["WGS84", "NAD83", "ETRS89"]
        if datum not in supported_datums:
            print(f"{Fore.RED}Error: Unsupported datum. Supported datums are: {', '.join(supported_datums)}.{Style.RESET_ALL}")
            return
        
        CONTEXT["Datum"] = datum
        print(f"{Fore.GREEN}Default datum set to {datum}.{Style.RESET_ALL}")


    def do_resetdatum(self, line):
        """
        Reset the datum to the default value (WGS84).

        Example:
            resetdatum
        """
        CONTEXT["Datum"] = "WGS84"
        print(f"{Fore.GREEN}Datum reset to default (WGS84).{Style.RESET_ALL}")


    def do_datum(self, line):
        """
        Show the current datum used for UTM to lat/lon transformations.

        Example:
            datum
        """
        if CONTEXT['Datum'] == "WGS84":
            print(f"{Fore.GREEN}Current datum: {CONTEXT['Datum']} (default){Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}Current datum: {Fore.YELLOW}{CONTEXT['Datum']} (Changed from default WGS84){Style.RESET_ALL}")


    def do_status(self, line):
        """
        Show the current status of the KMZ Creator, including whether a KMZ is loaded and if there are unsaved changes.

        Example:
            status
        """
        print(f"\n{Fore.CYAN}=== KMZ CREATOR STATUS ==={Style.RESET_ALL}")
        if CONTEXT["kmz_manager"] is None:
            print(f"{Fore.YELLOW}No KMZ loaded or created. Use create or open <path> to begin{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}KMZ loaded or created.{Style.RESET_ALL}")
        
        if CONTEXT["ChangesMade"]:
            print(f"{Fore.YELLOW}There are unsaved changes. Use save <path> to preserve them{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}No unsaved changes.{Style.RESET_ALL}")

        if CONTEXT['Datum'] == "WGS84":
            print(f"{Fore.GREEN}Current datum: {CONTEXT['Datum']} (default){Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}Current datum: {Fore.YELLOW}{CONTEXT['Datum']} (Changed from default WGS84){Style.RESET_ALL}")
        print(f"{Fore.CYAN}========================={Style.RESET_ALL}\n")


    # === KMZ COMMANDS ===
    def do_create(self, line):
        """
        Create a new blank KMZ file in memory.

        Example:
            create
        """
        
        if CONTEXT["ChangesMade"]:
            confirm = input(f"{Fore.YELLOW}You have unsaved changes. Are you sure you want to create a new KMZ?\nALL UNSAVED CHANGES WILL BE LOST (y/n): {Style.RESET_ALL}")
            if confirm.lower() != 'y':
                print(f"{Fore.YELLOW}Operation cancelled.{Style.RESET_ALL}")
                return

        print(f"{Fore.YELLOW}Creating new unnamed KMZ...{Style.RESET_ALL}")
        CONTEXT["kmz_manager"] = kg.KMZManager()
        CONTEXT["ChangesMade"] = True
        print(f"{Fore.GREEN}New KMZ created in memory. (Not yet saved, use save <path>){Style.RESET_ALL}")


    def do_open(self, line):
        """
        Open an existing KMZ file from a given path.

        Usage:
            open path/to/file.kmz

        Example:
            open my_kmz.kmz
        """

        if CONTEXT["ChangesMade"]:
            confirm = input(f"{Fore.YELLOW}You have unsaved changes. Are you sure you want to open a new KMZ?\nALL UNSAVED CHANGES WILL BE LOST (y/n): {Style.RESET_ALL}")
            if confirm.lower() != 'y':
                print(f"{Fore.YELLOW}Operation cancelled.{Style.RESET_ALL}")
                return

        path = line.strip()

        if not path:
            print(f"{Fore.RED}Error: No file path provided.{Style.RESET_ALL}")
            return

        if not path.endswith('.kmz'):
            path += '.kmz'
        
        if not os.path.isfile(path):
            print(f"{Fore.RED}Error: File {path} does not exist.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.YELLOW}Opening KMZ {path}...{Style.RESET_ALL}")
        try:
            CONTEXT["kmz_manager"] = kg.KMZManager(file_path=path)
            CONTEXT["ChangesMade"] = False
            print(f"{Fore.GREEN}KMZ file {path} loaded successfully.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error loading KMZ file: {e}{Style.RESET_ALL}")


    def do_save(self, line):
        """
        Save the current KMZ to a specified path. If the kmz was opened, a path is not mandatory.

        Usage:
            save [path/to/file.kmz]
            save

        Example:
            save my_kmz.kmz
            save
        """
        path = line.strip()

        if not path:
            if CONTEXT["kmz_manager"] and CONTEXT["kmz_manager"].file_path:
                path = CONTEXT["kmz_manager"].file_path
                print(f"{Fore.YELLOW}Last path recovered ({path}){Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Error: No file path provided.{Style.RESET_ALL}")
                return

        if not path.endswith('.kmz'):
            path += '.kmz'
        
        if CONTEXT["kmz_manager"] is None:
            print(f"{Fore.RED}Error: No KMZ loaded or created.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.YELLOW}Saving KMZ to {path}...{Style.RESET_ALL}")
        try:
            CONTEXT["kmz_manager"].save(file_path=path)
            CONTEXT["ChangesMade"] = False
            print(f"{Fore.GREEN}KMZ saved successfully to {path}.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error saving KMZ file: {e}{Style.RESET_ALL}")

    
    def do_showpoints(self, line):
        """
        List all points in the current KMZ.

        Example:
            showpoints
        """
        if CONTEXT["kmz_manager"] is None:
            print(f"{Fore.RED}Error: No KMZ loaded or created.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.YELLOW}Retrieving points...{Style.RESET_ALL}")
        points = CONTEXT["kmz_manager"].list_points()
        if not points:
            print(f"{Fore.RED}No points found in the KMZ.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}Points in the KMZ:{Style.RESET_ALL}")
        for point in points:
            print(f"{Fore.MAGENTA} - {point['name']}: (lon: {point['longitude']}, lat: {point['latitude']}){Style.RESET_ALL}")


    def do_addlonlat(self, line):
        """
        Add a point to the KMZ using latitude and longitude.

        Usage:
            addlatlon name lon lat

        Example:
            addlatlon T1 -3.7038 40.4168
        """
        if CONTEXT["kmz_manager"] is None:
            print(f"{Fore.RED}Error: No KMZ loaded or created.{Style.RESET_ALL}")
            return
        
        parts = line.split()
        if len(parts) != 3:
            print(f"{Fore.RED}Error: Invalid arguments. Usage: addlatlon name lon lat{Style.RESET_ALL}")
            return
        
        name, lon_str, lat_str = parts
        try:
            lon = float(lon_str)
            lat = float(lat_str)
        except ValueError:
            print(f"{Fore.RED}Error: Longitude and latitude must be numeric values.{Style.RESET_ALL}")
            return
        
        if CONTEXT["kmz_manager"].add_point(name, lon, lat):
            CONTEXT["ChangesMade"] = True
            print(f"{Fore.GREEN}Point {name} added at (lon: {lon}, lat: {lat}).{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Error: Point {name} could not be added.{Style.RESET_ALL}")


    def do_addutm(self, line):
        """
        Add points to the KMZ from UTM coordinates.

        Usage:
            addutm name x y zone

        Example:
            addutm T1 463712.5 4469224.7 30T
        """
        if CONTEXT["kmz_manager"] is None:
            print(f"{Fore.RED}Error: No KMZ loaded or created.{Style.RESET_ALL}")
            return

        parts = line.split()
        if len(parts) == 5:
            name, x_str, y_str, zone_str, datum = parts
        elif len(parts) == 4:
            name, x_str, y_str, zone_str = parts
            datum = CONTEXT["Datum"]
        else:
            print(f"{Fore.RED}Error: Invalid arguments. Usage: addutm name x y zone{Style.RESET_ALL}")
            return

        try:
            x = float(x_str)
            y = float(y_str)
        except ValueError:
            print(f"{Fore.RED}Error: x and y must be numeric values.{Style.RESET_ALL}.")
            return

        lon, lat = tf.transform_coordinates(x, y, zone_str, datum)

        if CONTEXT["kmz_manager"].add_point(name, lon, lat):
            CONTEXT["ChangesMade"] = True
            print(f"{Fore.GREEN}Point {name} added at (lon: {lon}, lat: {lat}) from UTM coordinates.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Error: Point {name} could not be added.{Style.RESET_ALL}")


    def do_addlist(self, line):
        """
        Add multiple points to the KMZ from a file containing XY coordinates.

        Usage:
            addlist path/to/file.txt

        Example:
            addlist coordinates.txt

        The file should contain lines with the format:
            name x y utm_code [datum]
        where x and y are numeric coordinates and name is an optional point name.
        Supported file extensions: txt
        """
        if CONTEXT["kmz_manager"] is None:
            print(f"{Fore.RED}Error: No KMZ loaded or created.{Style.RESET_ALL}")
            return

        file_path = line.strip()
        if not file_path:
            print(f"{Fore.RED}Error: No file path provided.{Style.RESET_ALL}")
            return

        if not os.path.isfile(file_path):
            print(f"{Fore.RED}Error: File {file_path} does not exist.{Style.RESET_ALL}")
            return

        points = fe.extract_coordinates(file_path)
        if not points:
            print(f"{Fore.RED}No valid points found in the file.{Style.RESET_ALL}")
            return
        
        for name, x, y, utm_tag in points:
            try:
                lon, lat = tf.transform_coordinates(x, y, utm_tag)
                if CONTEXT["kmz_manager"].add_point(name, lon, lat):
                    CONTEXT["ChangesMade"] = True
                    print(f"{Fore.GREEN}Point {name} added at (lon: {lon}, lat: {lat}) from UTM coordinates.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Error: Point {name} could not be added.{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error adding point {name}: {e}{Style.RESET_ALL}")
                continue


    def do_delete(self, line):
        """
        Delete a point from the KMZ by its name.

        Usage:
            delete point_name

        Example:
            delete T1
        """
        if CONTEXT["kmz_manager"] is None:
            print(f"{Fore.RED}Error: No KMZ loaded or created.{Style.RESET_ALL}")
            return
        
        name = line.strip()
        if not name:
            print(f"{Fore.RED}Error: No point name provided.{Style.RESET_ALL}")
            return
        
        points_before = CONTEXT["kmz_manager"].list_points()
        CONTEXT["kmz_manager"].delete_point(name)
        points_after = CONTEXT["kmz_manager"].list_points()
        
        if len(points_before) == len(points_after):
            print(f"{Fore.RED}Error: Point '{name}' not found.{Style.RESET_ALL}")
        else:
            CONTEXT["ChangesMade"] = True
            print(f"{Fore.GREEN}Point {name} deleted successfully.{Style.RESET_ALL}")


    def do_modpoint(self, line):
        """
        Modify a point's information
        

        This command has the following subcommands:
            - rename old_name new_name
            - relocate name new_lon new_lat
            - relocateutm name new_x new_y new_zone [Datum]

        Usage:
            modpoint <subcommand> [arguments]

        Examples:
            modpoint rename Point1 Point2
            modpoint relocate Point -3.7038 40.4168
        """
        if CONTEXT["kmz_manager"] is None:
            print(f"{Fore.RED}Error: No KMZ loaded or created.{Style.RESET_ALL}")
            return
        
        parts = line.split()
        if len(parts) < 2:
            print(f"{Fore.RED}Error: Invalid arguments. See 'help modpoint' for usage.{Style.RESET_ALL}")
            return
        
        subcommand = parts[0].lower()
        
        match subcommand:
            case "rename":
                if len(parts) != 3:
                    print(f"{Fore.RED}Error: Invalid arguments for rename. Usage: modpoint rename old_name new_name{Style.RESET_ALL}")
                    return
                old_name, new_name = parts[1], parts[2]
                points = CONTEXT["kmz_manager"].list_points()
                for point in points:
                    if point['name'] == old_name:
                        lon, lat = point['longitude'], point['latitude']
                        CONTEXT["kmz_manager"].update_point(old_name, new_name=new_name)
                        CONTEXT["ChangesMade"] = True
                        print(f"{Fore.GREEN}Point renamed from {old_name} to {new_name}.{Style.RESET_ALL}")
                        return
                print(f"{Fore.RED}Error: Point '{old_name}' not found.{Style.RESET_ALL}")

            case "relocate":
                if len(parts) != 4:
                    print(f"{Fore.RED}Error: Invalid arguments for relocate. Usage: modpoint relocate name new_lon new_lat{Style.RESET_ALL}")
                    return
                name, new_lon_str, new_lat_str = parts[1], parts[2], parts[3]
                try:
                    new_lon = float(new_lon_str)
                    new_lat = float(new_lat_str)
                except ValueError:
                    print(f"{Fore.RED}Error: Longitude and latitude must be numeric values.{Style.RESET_ALL}")
                    return
                points = CONTEXT["kmz_manager"].list_points()
                for point in points:
                    if point['name'] == name:
                        CONTEXT["kmz_manager"].update_point(name, new_lon=new_lon, new_lat=new_lat)
                        CONTEXT["ChangesMade"] = True
                        print(f"{Fore.GREEN}Point {name} relocated to (lon: {new_lon}, lat: {new_lat}).{Style.RESET_ALL}")
                        return
                print(f"{Fore.RED}Error: Point '{name}' not found.{Style.RESET_ALL}")

            case "relocateutm":
                if len(parts) == 5:
                    name, new_x_str, new_y_str, new_zone_str = parts[1], parts[2], parts[3], parts[4]
                    datum = CONTEXT["Datum"]
                elif len(parts) == 6:
                    name, new_x_str, new_y_str, new_zone_str, datum = parts[1], parts[2], parts[3], parts[4], parts[5]
                else:
                    print(f"{Fore.RED}Error: Invalid arguments for relocateutm. Usage: modpoint relocateutm name new_x new_y new_zone [Datum]{Style.RESET_ALL}")
                    return
                try:
                    new_x = float(new_x_str)
                    new_y = float(new_y_str)
                except ValueError:
                    print(f"{Fore.RED}Error: x and y must be numeric values.{Style.RESET_ALL}.")
                    return
                try:
                    new_lon, new_lat = tf.transform_coordinates(new_x, new_y, new_zone_str, datum)
                except Exception as e:
                    print(f"{Fore.RED}Error transforming UTM to lon/lat: {e}{Style.RESET_ALL}")
                    return
                points = CONTEXT["kmz_manager"].list_points()
                for point in points:
                    if point['name'] == name:
                        CONTEXT["kmz_manager"].update_point(name, new_lon=new_lon, new_lat=new_lat)
                        CONTEXT["ChangesMade"] = True
                        print(f"{Fore.GREEN}Point {name} relocated to (lon: {new_lon}, lat: {new_lat}) from UTM coordinates.{Style.RESET_ALL}")
                        return
                print(f"{Fore.RED}Error: Point '{name}' not found.{Style.RESET_ALL}")

            case _:
                print(f"{Fore.RED}Error: Unknown subcommand '{subcommand}'. See 'help modpoint' for usage.{Style.RESET_ALL}")
    

    def do_distancesall(self, line):
        """
        Calculate and display distances between all points in the KMZ.

        Usage:
            distancesall [Datum]

        Example:
            distancesall WGS84
            distancesall
        """
        if CONTEXT["kmz_manager"] is None:
            print(f"{Fore.RED}Error: No KMZ loaded or created.{Style.RESET_ALL}")
            return
        
        datum = line.strip() or CONTEXT["Datum"]
        supported_datums = ["WGS84", "NAD83", "ETRS89"]
        if datum not in supported_datums:
            print(f"{Fore.RED}Error: Unsupported datum. Supported datums are: {', '.join(supported_datums)}.{Style.RESET_ALL}")
            return

        print(f"{Fore.YELLOW}Calculating distances...{Style.RESET_ALL}")
        points = CONTEXT["kmz_manager"].list_points()
        if len(points) < 2:
            print(f"{Fore.RED}Error: At least two points are required to calculate distances.{Style.RESET_ALL}")
            return

        distances = CONTEXT["kmz_manager"].compute_distances_all(datum=datum)
        if not distances:
            print(f"{Fore.RED}Error: Could not compute distances.{Style.RESET_ALL}")
            return
        print(f"{Fore.GREEN}Distances between all points (using datum {datum}):{Style.RESET_ALL}")
        for d in distances:
            print(f"{Fore.MAGENTA} - {d[0]} to {d[1]}: {d[2]:.2f} meters{Style.RESET_ALL}")


    def do_distances(self, line):
        """
        Calculate and display the distance in a line of all points in the KMZ.
        Warning: This might not calculate the path you are looking for, it will pick them in order of addition.

        Usage:
            distances [Datum]

        Example:
            distances WGS84
            distances 
        """
        if CONTEXT["kmz_manager"] is None:
            print(f"{Fore.RED}Error: No KMZ loaded or created.{Style.RESET_ALL}")
            return
        
        datum = line.strip() or CONTEXT["Datum"]
        supported_datums = ["WGS84", "NAD83", "ETRS89"]
        if datum not in supported_datums:
            print(f"{Fore.RED}Error: Unsupported datum. Supported datums are: {', '.join(supported_datums)}.{Style.RESET_ALL}")
            return

        points = CONTEXT["kmz_manager"].list_points()
        if len(points) < 2:
            print(f"{Fore.RED}Error: At least two points are required to calculate distances.{Style.RESET_ALL}")
            return

        print(f"{Fore.YELLOW}Calculating distances in line configuration...{Style.RESET_ALL}")
        distances = CONTEXT["kmz_manager"].compute_distances_line(datum=datum)
        if distances is None:
            print(f"{Fore.RED}Error: Could not compute distances.{Style.RESET_ALL}")
            return

        print(f"{Fore.YELLOW}Warning: The distances will be calculated based on the order they were added. You might not get the measurement you are expeting\nUse distancesall for a more complete calculation{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Distances between all points in a line configuration (using datum {datum}):{Style.RESET_ALL}")
        for d in distances:
            print(f"{Fore.MAGENTA} - {d[0]} to {d[1]}: {d[2]:.2f} meters{Style.RESET_ALL}")
        
        total_distance = sum(d[2] for d in distances)
        print(f"{Fore.YELLOW}Total distance: {total_distance:.2f} meters{Style.RESET_ALL}")


    # === MISC / UNIMPORTANT ===

    def do_art(self, line):
        """
        Display ASCII art of the KMZ Creator logo.

        Example:
            art
        """
        art = f"""                                                                                                                                                                      
                  ##################################################################                   
                 #####################################################################                
                ######                                                          ######                
               #####    {Fore.RED}###{Style.RESET_ALL}   {Fore.YELLOW}###{Style.RESET_ALL}   {Fore.GREEN}###{Style.RESET_ALL}                                           #####               
               #####   {Fore.RED}####{Style.RESET_ALL}  {Fore.YELLOW}#####{Style.RESET_ALL}  {Fore.GREEN}####{Style.RESET_ALL}                                          #####               
               #####   {Fore.RED}####{Style.RESET_ALL}  {Fore.YELLOW}#####{Style.RESET_ALL}  {Fore.GREEN}####{Style.RESET_ALL}                                          #####               
               #####                                                              #####               
               #####{Fore.BLACK}##############################################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##############################################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##############################################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##############################################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##############################################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##### ########################################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}#####  ##############  ###   #   #####   #        ############{Style.RESET_ALL}#####               
               #####{Fore.BLACK}#######  ############  ##  ####   ###    ######  #############{Style.RESET_ALL}#####               
               #####{Fore.BLACK}#########  ##########    ###### # ### #  #####  ##############{Style.RESET_ALL}#####               
               #####{Fore.BLACK}#########   #########  #  ##### ## #  #  ###  ################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}#######   ###########  ##   ### ##   ##  ##  #################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}#####   #############  ###   ## #######  #        ############{Style.RESET_ALL}#####               
               #####{Fore.BLACK}####  ######      ############################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##############################################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##############################################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}#######    ###################################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}#####   ###   ##########################  ####################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##### ###### ##     ##     ###       #      ##      ##     ###{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##### ########## ####  ###  #######  ### ####  #### ##  ######{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##### ######  ## ####  #######   ##  ### ####  ####  #  ######{Style.RESET_ALL}#####               
               #####{Fore.BLACK}#####        ##  ####   ##  ##  ##   ###  # #   #   ##  ######{Style.RESET_ALL}#####               
               #####{Fore.BLACK}########  ##############  ######  ######## #####  ############{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##############################################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##############################################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##############################################################{Style.RESET_ALL}#####               
               #####{Fore.BLACK}##############################################################{Style.RESET_ALL}#####               
               ######{Fore.BLACK}############################################################{Style.RESET_ALL}######               
               #######{Fore.BLACK}##########################################################{Style.RESET_ALL}#######               
                #######{Fore.BLACK}#######################################################{Style.RESET_ALL}########                
                ######################################################################                
                  ##################################################################                                                                                                                                                                                                                                                                                                                                                                 
        """
        print(f"\n\n{art}\n\n")

if __name__ == "__main__":
    KMZShell().cmdloop()
