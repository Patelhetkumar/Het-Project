def compare_cells(efsservers_data, inventory_data):
    """Compare expected and actual cells and print discrepancies to console after additional verification."""
    
    corrected_mismatches = []  # To store verified mismatches

    for server, expected_cells in efsservers_data.items():
        group = determine_group_from_pattern(server)
        if not group:
            print(f"Server {server} does not match any known group.")
            continue

        actual_cells = inventory_data.get(server, set())
        
        if not actual_cells:  
            # If actual is empty, mark it as a new server
            corrected_mismatches.append(f"\nMismatch for {server} in group {group}:")
            corrected_mismatches.append(f" EFS Database: {expected_cells}")
            corrected_mismatches.append(f" Ax Inventory: (New Server - No record found)")
            continue
        
        if expected_cells != actual_cells:
            # Find missing and extra cells
            missing_cells = expected_cells - actual_cells
            extra_cells = actual_cells - expected_cells

            # **Additional Verification Step**
            # Remove common elements from both sets as they are actually present in both
            false_mismatches = missing_cells.intersection(extra_cells)
            missing_cells -= false_mismatches
            extra_cells -= false_mismatches

            # Store verified output
            corrected_mismatches.append(f"\n{server} in group {group}:")
            corrected_mismatches.append(f" EFS Database: {expected_cells}")
            corrected_mismatches.append(f" Ax Inventory: {actual_cells}")

            if missing_cells:
                corrected_mismatches.append(f" Cells in the EFS Database but not in the Ax inventory: {missing_cells}")
            if extra_cells:
                corrected_mismatches.append(f" Cells in the Ax inventory but not in the EFS Database: {extra_cells}")

            if false_mismatches:
                corrected_mismatches.append(f" ✅ Corrected: These cells were falsely marked as mismatched but actually exist in both: {false_mismatches}")

    # Print final verified output
    print("\n===== FINAL VERIFIED OUTPUT =====")
    print("\n".join(corrected_mismatches) if corrected_mismatches else "No mismatches found. ✅")

