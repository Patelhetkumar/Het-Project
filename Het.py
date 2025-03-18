def parse_inventory(file_path):
    """Parse inventory YAML, handle hierarchical groups, normalize cell names, and remove duplicates."""
    with open(file_path, "r") as file:
        inventory = yaml.safe_load(file)

    inventory_data = {}
    all_groups = inventory.get('all', {}).get('children', {})

    def normalize_cell(cell):
        """Standardizes cell names to remove spaces and ensure consistent formatting."""
        return cell.lower().replace(" ", "").strip()

    def extract_hosts(group_name, seen_groups=None):
        """ Recursively extract hosts and their cells while avoiding duplication. """
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
                    # Normalize cell formatting
                    normalized_cells = {normalize_cell(cell) for cell in server_info["cells"]}
                    if server in hosts:
                        hosts[server].update(normalized_cells)
                    else:
                        hosts[server] = normalized_cells

        # Recursively process child groups
        if "children" in group_data and isinstance(group_data["children"], dict):
            for child_group in group_data["children"]:
                child_hosts = extract_hosts(child_group, seen_groups)
                for server, cells in child_hosts.items():
                    if server in hosts:
                        hosts[server].update(cells)
                    else:
                        hosts[server] = cells

        return hosts

    # Process each group in the inventory
    for group in all_groups:
        inventory_data.update(extract_hosts(group))

    print("\n✅ Debug: Inventory Loaded Successfully!")
    print(f"Total servers found: {len(inventory_data)}")
    
    return inventory_data
###############################################################

def compare_cells(efsservers_data, inventory_data):
    """Compare expected and actual cells, ensuring normalization and avoiding duplicate mismatches."""
    
    def normalize_cell(cell):
        """Standardizes cell names to remove spaces and ensure consistent formatting."""
        return cell.lower().replace(" ", "").strip()

    print("\n✅ Debug: Starting Comparison Between EFS and AX Inventory")
    print(f"Total EFS servers: {len(efsservers_data)} | Total Inventory servers: {len(inventory_data)}")

    missing_servers = list(set(efsservers_data.keys()) - set(inventory_data.keys()))
    extra_servers = list(set(inventory_data.keys()) - set(efsservers_data.keys()))

    if missing_servers:
        print("\n🚨 Missing servers in inventory:")
        for server in missing_servers:
            print(f" {server}")

    if extra_servers:
        print("\n⚠️ Extra servers found in AX inventory but not in EFS Database:")
        for server in extra_servers:
            print(f" {server}")

    for server, expected_cells in efsservers_data.items():
        group = determine_group_from_pattern(server)
        actual_cells = inventory_data.get(server, set())

        # Normalize cells before comparison
        expected_cells_normalized = {normalize_cell(cell) for cell in expected_cells}
        actual_cells_normalized = {normalize_cell(cell) for cell in actual_cells}

        if not actual_cells_normalized:
            print(f"\n❌ Mismatch for server {server} in group {group}:")
            print(f" EFS Database: {expected_cells_normalized}")
            print(f" Ax inventory: (New Server)")
        elif expected_cells_normalized != actual_cells_normalized:
            missing_cells = expected_cells_normalized - actual_cells_normalized
            extra_cells = actual_cells_normalized - expected_cells_normalized

            print(f"\n🔍 {server} in group {group}:")
            print(f" EFS Database: {expected_cells_normalized}")
            print(f" Ax inventory: {actual_cells_normalized}")

            if missing_cells:
                print(f" 🚨 Cells in the EFS Database but not in the Ax inventory: {missing_cells}")
            if extra_cells:
                print(f" ⚠️ Cells in the Ax inventory but not in the EFS Database: {extra_cells}")

    print("\n✅ Debug: Comparison Completed!")
