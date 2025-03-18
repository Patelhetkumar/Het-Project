def normalize_cell(cell_name):
    """Normalize cell names to remove inconsistencies (spaces, domain variations)."""
    cell_name = cell_name.strip()  # Remove spaces
    cell_name = cell_name.replace(".m1.com", ".ml.com")  # Standardize domain variation
    return cell_name.lower()  # Convert to lowercase (if case sensitivity isn't required)

##########################

def parse_inventory(file_path):
    """Parse inventory-prod.yaml to extract actual cells for servers, avoiding duplicates."""
    with open(file_path, "r") as file:
        inventory = yaml.safe_load(file)

    inventory_data = {}
    processed_hosts = set()

    for group, group_data in inventory.get('all', {}).get('children', {}).items():
        if "hosts" in group_data and isinstance(group_data["hosts"], dict):
            for server, server_info in group_data["hosts"].items():
                if isinstance(server_info, dict):
                    # Normalize cell names
                    cells = {normalize_cell(c) for c in server_info.get("cells", [])}

                    # Ensure no duplicate hosts
                    if server not in processed_hosts:
                        inventory_data[server] = cells
                        processed_hosts.add(server)

    return inventory_data

#############################################

def parse_efs_database(file_path):
    """Parse EFS database and extract server-cell mappings, ensuring normalization."""
    efs_data = {}

    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split(",")
            if len(parts) < 2:
                continue  # Skip malformed lines

            server, cell = parts[0].strip(), normalize_cell(parts[1].strip())

            if server not in efs_data:
                efs_data[server] = set()
            efs_data[server].add(cell)

    return efs_data


#############################################################

def compare_cells(efs_data, ax_inventory):
    """Compare EFS and AX inventory and detect mismatches."""
    mismatches = []

    for server, expected_cells in efs_data.items():
        actual_cells = ax_inventory.get(server, set())

        # Normalize both sets of cells before comparison
        expected_cells = {normalize_cell(c) for c in expected_cells}
        actual_cells = {normalize_cell(c) for c in actual_cells}

        missing_cells = expected_cells - actual_cells
        extra_cells = actual_cells - expected_cells

        if missing_cells or extra_cells:
            mismatches.append({
                "Server": server,
                "Missing Cells": ", ".join(missing_cells) if missing_cells else "None",
                "Extra Cells": ", ".join(extra_cells) if extra_cells else "None"
            })

    return mismatches
