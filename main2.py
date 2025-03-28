import yaml
import re
import os
import subprocess

# Define the pattern-to-group mapping
PATTERN_TO_GROUP = {
    r"laau42efs.*": "l_aja_ausyb01sr1",
    r"laauu1efs.*": "l_aja_ausy02sr1",
    r"lchhk01efs.*": "l_aja_cnhhk01",
    r"lchhk02efs.*": "l_aja_cnhhk02",
    r"lchhk07efs.*": "l_aja_inhche07sr1",
    r"linnh02efs.*": "l_aja_inmu02sr1",
    r"linnh08efs.*": "l_aja_inmu08sr1",
    r"ljnpa05efs.*": "l_aja_jnspa01",
    r"ljnpa01efs.*": "l_aja_jnpe01",
    r"ljptk01efs.*": "l_aja_jptk01",
    r"lkrhk09efs.*": "l_aja_kray01sr1",
    r"lkrhk02efs.*": "l_aja_krse01sr2",
    r"lsgsg01efs.*": "l_aja_ssgsg01",
    r"lsgsg02efs.*": "l_aja_ssgsg02",
    r"ltwtp04efs.*": "l_aja_ttwtp04",
    r"ltwtp01efs.*": "l_aja_ttwtp01sr1",
    r"lemea01efs.*": "l_emea_ukcm01",
    r"luksg01efs.*": "l_emea_ukvg01",
    r"lusaz07efs.*": "l_amrs_usaz07",
    r"lusaz06efs.*": "l_amrs_usaz06",
    r"luspa01efs.*": "l_amrs_uspa01",
    r"lustx02efs.*": "l_amrs_ustx02",
    r"lusva01efs.*": "l_amrs_usva01",
}

def get_efs_server_output():
    """Executes the command and returns parsed EFS server details directly."""
    cmd = "efs display efsserver | sed -e '1,/^ ==* /d' | awk '{{print $2 \", \" $1 \", \" $3}}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)

    servers = []
    for line in result.stdout.strip().split("\n"):
        parts = line. strip(). split(',')
        if len(parts) >= 3:
            servers.append(parts)

    return servers

# Load inventory yaml
script_dir = os.path.dirname(os.path.abspath(_file_))
inventory_file = os.path.join(script_dir, '..', 'prod', 'inventory.prod.yaml')
with open(inventory_file, 'r') as file:
    inventory1 = yaml.safe_load(file)

# Extract control group hosts
controlgroup_a1 = inventory1['all']['children']['controlgroup_a']['hosts']
controlgroup_b1 = inventory1['all']['children']['controlgroup_b']['hosts']

# Extract server group hosts
servertype_dev = set(inventory1['all']['children']['servertype_dev']['hosts'])
servertype_prod = set(inventory1['all']['children']['servertype_prod']['hosts'])



# Load EFS servers
efs_servers1 = load_efs_unique_servers(efs_file)
efs_servers = load_efs_servers(efs_file)

# Set to store unique mismatches
mismatches_servergroup = set()

# Validate server placement
for server_nm in efs_servers:
    if len(server_nm) < 3:
        continue  # Skip malformed lines

    server_name_1, _, host_type = server_nm
    if server_name_1 in servertype_dev and host_type != 'dev':
        mismatches_servergroup.add(f"Mismatch: {server_name_1} {host_type} in servertype_dev but should be in servertype_prod")
    elif server_name_1 in servertype_prod and host_type != 'prod':
        mismatches_servergroup.add(f"Mismatch: {server_name_1} {host_type} in servertype_prod but should be in servertype_dev")

# Dictionaries to store server names under each group and type
group_counts = {
    'controlgroup_a': {'dev': [], 'prod': []},
    'controlgroup_b': {'dev': [], 'prod': []}
}

# Dictionary to track pairs by data center
data_center_pairs = {}

# Track assigned servers
assigned_servers = set()

# Check placement of each unique server
for server_name1, (cell_name, host_type) in efs_servers1.items():
    # Identify control group
    if server_name1 in controlgroup_a1:
        control_group = 'controlgroup_a'
    elif server_name1 in controlgroup_b1:
        control_group = 'controlgroup_b'
    else:
        continue  # Skip if the server is not part of any control group

    # Track in the respective control group
    group_counts[control_group][host_type].append((server_name1, cell_name))
    assigned_servers.add(server_name1)

    # Track pairs by data center (cell_name)
    if cell_name not in data_center_pairs:
        data_center_pairs[cell_name] = {'controlgroup_a': {'dev': [], 'prod': []},
                                        'controlgroup_b': {'dev': [], 'prod': []}}

    data_center_pairs[cell_name][control_group][host_type].append(server_name1)

# Identify mismatches
mismatches = []

# Validate pairing per data center
for cell_name, groups in data_center_pairs.items():
    controlgroup_a_dev = groups['controlgroup_a'] ['dev' ]
    controlgroup_a_prod = groups['controlgroup_a' ] ['prod' ]
    controlgroup_b_dev = groups['controlgroup_b'] ['dev' ]
    controlgroup_b_prod = groups['controlgroup_b']['prod' ]

    if len(controlgroup_a_dev) != len(controlgroup_a_prod) or len(controlgroup_b_dev) != len(controlgroup_b_prod):
        mismatches.append(f"\nMismatch in data center {cell_name}:")
        mismatches.append(f"controlgroup_a: {' '.join([f'{s} (dev)' for s in controlgroup_a_dev])} {' '.join([f'{s} (prod)' for s in controlgroup_a_prod]) }")
        mismatches. append(f"controlgroup_b: {' '.join([f'{s} (dev)' for s in controlgroup_b_dev])} {' '.join([f'{s} (prod)' for s in controlgroup_b_prod]) }")

# Validate total count of assigned servers
total_efs_count = len(efs_servers1) #Unique servers
total_assigned_count = len(assigned_servers)

if total_assigned_count != total_efs_count:
    mismatches.append(f"Total server count mismatch: expected {total_efs_count}, but assigned {total_assigned_count}")
    unassigned_servers = [server for server in efs_servers1.keys() if server not in assigned_servers]
    mismatches.append(f"Unassigned servers: {' '.join(unassigned_servers)}")

def load_efs_unique_servers():
    """
    Loads unique EFS servers.

    Returns:
        dict: A dictionary where keys are server names and values are tuples of (cell name, host type).
    """
    servers = {}
    efs_servers = get_efs_server_output()
    for parts in efs_servers:
        if len(parts) < 3:
            continue # skip malformed Lines
        server_name, cell_name, host_type = parts
        servers[server_name] = (cell_name, host_type)

    return servers

def load_efs_servers():
    """
    Loads EFS servers.

    Returns:
        list: A list of lists, where each inner list contains server name, cell name, and host type.
    """
    return get_efs_server_output()

# Function to load the YAML inventory file
def load_inventory(file_path):
    """
    Loads the inventory YAML file.

    Args:
        file_path (str): The path to the inventory YAML file.

    Returns:
        dict: The loaded inventory data.
    """
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def normalize_cell(cell_name):
    """
    Normalizes cell names by removing extra spaces and standardizing domain variations.

    Args:
        cell_name (str): The cell name to normalize.

    Returns:
        str: The normalized cell name.
    """
    cell_name = cell_name. strip() # Remove leading/trailing spaces
    cell_name = re.sub(r'\s+', '', cell_name) # Remove internal spaces
    cell_name = cell_name.replace(".m1.com", ".ml.com") # Standardize domain variation
    return cell_name


def parse_inventory(file_path):
    """
    Parses the inventory YAML file to extract server names and their associated cells.

    Args:
        file_path (str): The path to the inventory YAML file.

    Returns:
        dict: A dictionary where keys are server names and values are sets of cell names.
    """
    with open(file_path, "r") as file:
        inventory = yaml.safe_load(file)

    inventory_data = {}
    all_groups = inventory.get('all', {}) .get('children', {})

# Keep track of which hosts we've already processed
    processed_hosts = set()

    for group, group_data in all_groups.items():
        if "hosts" in group_data and isinstance(group_data["hosts"], dict):
            for server, server_info in group_data["hosts"].items():
                if isinstance(server_info, dict):
                    # Normalize cell names before adding
                    cells = set(normalize_cell(c) for c in server_info.get("cells", []))

                    if server not in processed_hosts:
                        inventory_data[server] = cells
                        processed_hosts.add(server) # Mark this host as processed

        # Handle `children sections (nested groups)
        if "children" in group_data:
            for child_group in group_data["children"]:
                if child_group in all_groups: # Avoid processing duplicate child groups
                    continue

    return inventory_data

def determine_group_from_pattern(server_name):
    """
    Determines the group for a server based on its name using predefined patterns.

    Args:
        server_name (str): The name of the server.

    Returns:
        str: The group name if a match is found, otherwise "Unknown Group".
    """
    for pattern, group in PATTERN_TO_GROUP.items():
        if re.match(pattern, server_name):
            return group
    return "Unknown Group" # Default if no match found

# Function to parse efsservers.txt
def parse_efsservers():
    """
    Parses the output of 'efs display efsserver' to extract server names and their expected cells.

    Returns:
        dict: A dictionary where keys are server names and values are sets of cell names.
    """
    server_data = {}
    efs_servers =get_efs_server_output()

    for parts in efs_servers:
        if len(parts) >= 3:
            server, cell, _ = parts
            if server not in server_data:
                server_data[server] = set()
            server_data[server].add(cell)
    return server_data

def compare_cells(efsservers_data, inventory_data):
    """
    Compares the cells from the EFS output with the cells from the inventory data and prints discrepancies.

    Args:
        efsservers_data (dict): Dictionary of server names and their expected cells.
        inventory_data (dict): Dictionary of server names and their actual cells from the inventory.
    """
    missing_servers = list(set(efsservers_data.keys()) - set(inventory_data.keys()))
    extra_servers = list(set(inventory_data.keys()) - set(efsservers_data.keys()))

    if missing_servers:
        print("\nMissing servers in inventory:")
        print("==========================================================")
        for server in missing_servers:
            print(f" {server}")
    if extra_servers:
        print("\nservers found in ax_inventories but not in Efs Database or efsserver.txt:")
        print("==========================================================")
        for server in extra_servers:
            print(f" {server}")

    for server, expected_cells in efsservers_data.items():
        group = determine_group_from_pattern(server)
        if not group:
            print(f"Server {server} does not match any known group.")
            continue

        # Normalize expected and actual cells before comparison
        actual_cells = {normalize_cell(c) for c in inventory_data.get(server, set())}
        expected_cells = {normalize_cell(c) for c in expected_cells}

        if not actual_cells:
            print(f"\nMismatch for server: {server} in group {group}:")
            print(f" Efs Database: {expected_cells}")
            print(f" Ax inventory: (New Server)")
        elif expected_cells != actual_cells:
            missing_cells = expected_cells - actual_cells
            extra_cells = actual_cells - expected_cells

            print(f"\n{server} in group {group}:")
            print(f" Efs Database: {expected_cells}")
            print(f" Ax inventory: {actual_cells}")
            
            if missing_cells:
                print(f" Cells in the Efs Database but not in the Ax inventory: {missing_cells}")
            if extra_cells:
                print(f" Cells in the Ax inventory but not in the Efs Database: {extra_cells}")

    if mismatches_servergroup:
        print("\nServers group validation:")
        print("==========================================================")
        print("\n".join(mismatches_servergroup))
    else:
        print("==========================================================")
        print("All servers are in the correct groups. \n")

    if mismatches:
        print("\nControl Group Validation:")
        print("==========================================================")
        print("\n".join(mismatches))
    else:
        print("==========================================================")
        print("Controlgroup A and B are correctly balanced for high availability. \n")

def validate_inventory_with_efs(inventory_file):
    """
    Validates the server inventory against EFS server data.

    This function orchestrates the process of loading data from the inventory file
    and EFS server, parsing it, and then comparing the cell assignments.  It also
    checks for server group and control group consistency.

    Args:
        inventory_file (str): Path to the inventory YAML file.
    """
    efsservers_data = parse_efsservers()
    inventory_data = parse_inventory(inventory_file)
    compare_cells(efsservers_data, inventory_data)

# Call the function
validate_inventory_with_efs(inventory_file)