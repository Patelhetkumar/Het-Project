def parse_efsservers(efs_file):
    """Parses EFS database and extracts servers with their expected cells."""
    efs_servers = {}

    with open(efs_file, 'r') as file:
        for line in file:
            parts = line.strip().split(",")  # Split by comma
            if len(parts) < 3:
                continue  # Skip malformed lines

            server_name = parts[0].strip().lower()
            cell_name = parts[1].strip().lower()
            efs_servers.setdefault(server_name, set()).add(cell_name)

    print(f"\n✅ Debug: Loaded {len(efs_servers)} EFS servers.")
    for server, cells in efs_servers.items():
        print(f"📌 {server} -> {cells}")  # Debug Output

    return efs_servers

#################

import yaml

def parse_inventory(file_path):
    """Parses inventory YAML, handles child groups correctly, and removes duplicates."""
    with open(file_path, "r") as file:
        inventory = yaml.safe_load(file)

    inventory_data = {}
    all_groups = inventory.get('all', {}).get('children', {})

    def extract_hosts(group_name, seen_groups=None):
        """ Recursively extract hosts and their cells while avoiding duplicate entries. """
        if seen_groups is None:
            seen_groups = set()

        if group_name in seen_groups:
            return {}  # Prevent infinite loops

        seen_groups.add(group_name)
        group_data = all_groups.get(group_name, {})

        hosts = {}
        if "hosts" in group_data and isinstance(group_data["hosts"], dict):
            for server, server_info in group_data["hosts"].items():
                if isinstance(server_info, dict) and "cells" in server_info:
                    normalized_cells = {normalize_cell(cell) for cell in server_info["cells"]}
                    hosts.setdefault(server, set()).update(normalized_cells)

        # Recursively process child groups
        if "children" in group_data and isinstance(group_data["children"], dict):
            for child_group in group_data["children"]:
                child_hosts = extract_hosts(child_group, seen_groups)
                for server, cells in child_hosts.items():
                    hosts.setdefault(server, set()).update(cells)

        return hosts

    # Process each group in the inventory
    for group in all_groups:
        inventory_data.update(extract_hosts(group))

    print(f"\n✅ Debug: Loaded {len(inventory_data)} YAML servers.")
    for server, cells in inventory_data.items():
        print(f"📌 {server} -> {cells}")  # Debug Output

    return inventory_data

###############


import re

def normalize_cell(cell):
    """Standardizes cell names by removing spaces and ensuring correct dot formatting."""
    before = cell.strip().lower()
    cell = re.sub(r'\s+', '', before)  # Remove all spaces
    cell = re.sub(r'\.\.+', '.', cell)  # Remove multiple dots
    cell = re.sub(r'\s*\.\s*', '.', cell)  # Fix spaces around dots
    after = cell

    if before != after:
        print(f"🔍 Normalized: {before} -> {after}")  # Debugging output

    return cell

#########################

def compare_cells(efsservers_data, inventory_data):
    """Compare expected and actual cells, ensuring proper normalization and avoiding duplicate mismatches."""

    print("\n✅ Debug: Starting Comparison Between EFS and AX Inventory")
    print(f"Total EFS servers: {len(efsservers_data)} | Total Inventory servers: {len(inventory_data)}")

    if not efsservers_data:
        print("\n❌ ERROR: No EFS servers found. Check your EFS data extraction.")
    if not inventory_data:
        print("\n❌ ERROR: No Inventory servers found. Check your YAML parsing.")

    for server, expected_cells in efsservers_data.items():
        group = determine_group_from_pattern(server)
        actual_cells = inventory_data.get(server, set())

        # Normalize cells before comparison
        expected_cells_normalized = {normalize_cell(cell) for cell in expected_cells}
        actual_cells_normalized = {normalize_cell(cell) for cell in actual_cells}

        print(f"\n🔍 Debug for {server} in group {group}:")
        print(f" - Before Normalization: {expected_cells} | {actual_cells}")
        print(f" - After Normalization: {expected_cells_normalized} | {actual_cells_normalized}")

        if expected_cells_normalized != actual_cells_normalized:
            missing_cells = expected_cells_normalized - actual_cells_normalized
            extra_cells = actual_cells_normalized - expected_cells_normalized

            print(f"\n❌ Mismatch for server {server} in group {group}:")
            print(f" ✅ EFS Database: {expected_cells_normalized}")
            print(f" ✅ Ax inventory: {actual_cells_normalized}")

            if missing_cells:
                print(f" 🚨 Cells in the EFS Database but not in the Ax inventory: {missing_cells}")
            if extra_cells:
                print(f" ⚠️ Cells in the Ax inventory but not in the EFS Database: {extra_cells}")

    print("\n✅ Debug: Comparison Completed!")


####################
print("\n🚀 Starting EFS & Inventory Comparison...\n")

# Load EFS data
efsservers_data = parse_efsservers('efsservers.txt')
print(f"✅ EFS Data Loaded. {len(efsservers_data)} servers found.\n")

# Load Inventory data
inventory_data = parse_inventory('inventory.prod.yaml')
print(f"✅ Inventory Data Loaded. {len(inventory_data)} servers found.\n")

# Perform Comparison
compare_cells(efsservers_data, inventory_data)
print("\n🚀 Comparison Complete!\n")
