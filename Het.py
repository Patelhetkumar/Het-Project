def compare_cells(efsservers_data, inventory_data):
    """Compare expected and actual cells and print discrepancies to console with additional verification."""

    missing_servers = list(set(efsservers_data.keys()) - set(inventory_data.keys()))
    extra_servers = list(set(inventory_data.keys()) - set(efsservers_data.keys()))

    if missing_servers:
        print("Missing servers in inventory:")
        print("===================================")
        for server in missing_servers:
            print(f" {server}")

    if extra_servers:
        print("\n Servers found in ax_inventories but not in EFS Database or efsserver.txt:")
        print("===================================")
        for server in extra_servers:
            print(f" {server}")

    for server, expected_cells in efsservers_data.items():
        group = determine_group_from_pattern(server)
        if not group:
            print(f"Server {server} does not match any known group.")
            continue

        actual_cells = inventory_data.get(server, set())
        
        if not actual_cells:  
            print("\nMismatch for server:")
            print("===================================")
            print(f"{server} in group {group}:")
            print(f" EFS Database: {expected_cells}")
            print(f" Ax Inventory: (New Server - No record found)")
            continue
        
        if expected_cells != actual_cells:
            # Find missing and extra cells
            missing_cells = expected_cells - actual_cells
            extra_cells = actual_cells - expected_cells

            # ✅ Additional Verification Step: Remove false mismatches
            false_mismatches = missing_cells.intersection(extra_cells)
            missing_cells -= false_mismatches
            extra_cells -= false_mismatches

            print(f"\n{server} in group {group}:")
            print(f" EFS Database: {expected_cells}")
            print(f" Ax Inventory: {actual_cells}")

            if missing_cells:
                print(f" Cells in the EFS Database but not in the Ax inventory: {missing_cells}")
            if extra_cells:
                print(f" Cells in the Ax inventory but not in the EFS Database: {extra_cells}")

            if false_mismatches:
                print(f" ✅ Corrected: These cells were falsely marked as mismatched but actually exist in both: {false_mismatches}")

    if mismatches_servergroup:
        print("\nServers group validation:")
        print("===================================")
        print("\n".join(mismatches_servergroup))
    else:
        print("\n===================================")
        print("All servers are in the correct groups. ✅")
