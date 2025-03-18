def parse_inventory(file_path):
    """Parse inventory-prod.yaml to extract actual cells for servers, avoiding duplicates."""
    with open(file_path, "r") as file:
        inventory = yaml.safe_load(file)

    inventory_data = {}
    all_groups = inventory.get('all', {}).get('children', {})

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
                        processed_hosts.add(server)  # Mark this host as processed

        # Handle `children` sections (nested groups)
        if "children" in group_data:
            for child_group in group_data["children"]:
                if child_group in all_groups:  # Avoid processing duplicate child groups
                    continue  
                
    return inventory_data
#############


def normalize_cell(cell_name):
    """Normalize cell names to remove inconsistencies (e.g., extra spaces, domain variations)."""
    cell_name = cell_name.strip()  # Remove leading/trailing spaces
    cell_name = re.sub(r'\s+', '', cell_name)  # Remove internal spaces
    cell_name = cell_name.replace(".m1.com", ".ml.com")  # Standardize domain variation
    return cell_name


#####################
def compare_cells(efsservers_data, inventory_data):
    """Compare expected and actual cells and print discrepancies to console."""
    missing_servers = list(set(efsservers_data.keys()) - set(inventory_data.keys()))
    extra_servers = list(set(inventory_data.keys()) - set(efsservers_data.keys()))

    if missing_servers:
        print("\nMissing servers in inventory:")
        print(" === ")
        for server in missing_servers:
            print(f" {server}")

    if extra_servers:
        print("\nServers found in ax_inventories but not in Efs Database or efsserver.txt:")
        print(" === ")
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
