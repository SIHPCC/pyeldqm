"""
Chemical Database Access Tutorial

This tutorial demonstrates how to use the ChemicalDatabase and ChemicalDataFrame
classes to access and manage chemical properties. Run each cell sequentially to
explore different database operations.

Run this file in an IDE that supports cell execution (VS Code with Python extension,
Jupyter, or Spyder) or execute sections manually in an interactive Python session.
"""

import sys
import os

# Add parent directories to path for proper imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from pyELDQM.core.chemical_database import ChemicalDatabase

try:
    from pyELDQM.core.chemical_dataframe import ChemicalDataFrame
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


# %% 
# # 1. Basic Chemical Lookup
# Retrieve and display properties of a specific chemical by name.
# This demonstrates the simplest way to access the database.

with ChemicalDatabase() as db:
    ammonia = db.get_chemical_by_name("AMMONIA")
    
    if ammonia:
        print("=" * 80)
        print("AMMONIA - Chemical Properties")
        print("=" * 80)
        print(f"Name: {ammonia['name']}")
        print(f"CAS Number: {ammonia['cas_number']}")
        print(f"Molecular Weight: {ammonia['molecular_weight']} g/mol")
        print(f"IDLH: {ammonia['idlh']}")
        print(f"Boiling Point: {ammonia['ambient_boiling_point_f']}°F")
        print(f"Freezing Point: {ammonia['freezing_point_f']}°F")
        print(f"LEL: {ammonia['lel']}")
        print(f"UEL: {ammonia['uel']}")


# %%
# # 2. Search the Database
# Search for chemicals by partial name match.
# Useful when you don't know the exact chemical name.

with ChemicalDatabase() as db:
    search_term = "chlor"
    results = db.search_chemicals(search_term)
    
    print("\n" + "=" * 80)
    print(f"Search Results for '{search_term}' - Found {len(results)} chemicals")
    print("=" * 80)
    
    for idx, chem in enumerate(results[:10], 1):
        print(f"{idx:2d}. {chem['name']:40s} (CAS: {chem['cas_number']})")
    
    if len(results) > 10:
        print(f"... and {len(results) - 10} more chemicals")


# %%
# # 3. Lookup by CAS Number
# Find a chemical using its CAS (Chemical Abstracts Service) registry number.

with ChemicalDatabase() as db:
    cas_number = "7664-41-7"  # Ammonia CAS number
    chemical = db.get_chemical_by_cas(cas_number)
    
    print("\n" + "=" * 80)
    print(f"Chemical Lookup by CAS: {cas_number}")
    print("=" * 80)
    
    if chemical:
        print(f"Chemical Name: {chemical['name']}")
        print(f"Molecular Weight: {chemical['molecular_weight']} g/mol")
    else:
        print("Chemical not found")


# %%
# # 4. Retrieve Specific Properties
# Extract and compare specific properties across multiple chemicals.

with ChemicalDatabase() as db:
    chemicals_to_compare = ["AMMONIA", "CHLORINE", "ACETONE"]
    
    print("\n" + "=" * 80)
    print("Property Comparison Across Chemicals")
    print("=" * 80)
    print(f"\n{'Chemical':<20} {'MW (g/mol)':<15} {'IDLH':<20} {'AEGL-3 (60min)':<20}")
    print("-" * 75)
    
    for chem_name in chemicals_to_compare:
        chem = db.get_chemical_by_name(chem_name)
        if chem:
            mw = chem['molecular_weight'] or "N/A"
            idlh = chem['idlh'] or "N/A"
            aegl3 = chem['aegl3_60min'] or "N/A"
            print(f"{chem_name:<20} {mw:<15} {idlh:<20} {aegl3:<20}")


# %%
# # 5. View Database Overview
# Display statistics about the entire database.

with ChemicalDatabase() as db:
    try:
        db.display_database_summary()
    except Exception as e:
        print(f"\nDatabase Summary (Error displaying with formatting): {e}")
        summary = db.get_database_summary()
        print(f"Total Chemicals: {summary['total_chemicals']}")
        print(f"With Molecular Weight: {summary['with_molecular_weight']}")
        print(f"With IDLH Values: {summary['with_idlh']}")
        print(f"Database Path: {summary['database_path']}")


# %%
# # 6. List Available Properties
# See all chemical properties available in the database.

with ChemicalDatabase() as db:
    try:
        db.list_available_properties()
    except Exception as e:
        # Manual display if formatting fails
        print("\n" + "=" * 80)
        print("Available Properties")
        print("=" * 80)
        print("\nChemical database contains the following 19 properties:")
        properties = [
            "id", "name", "cas_number", "molecular_weight", "idlh",
            "aegl1_60min", "aegl2_60min", "aegl3_60min",
            "erpg1", "erpg2", "erpg3",
            "pac1", "pac2", "pac3",
            "lel", "uel",
            "ambient_boiling_point_f", "freezing_point_f", "normal_boiling_point_f"
        ]
        for idx, prop in enumerate(properties, 1):
            print(f"  {idx:2d}. {prop}")
        print()


# %%
# # 7. Display Chemicals in Table Format
# View chemicals in a nicely formatted table (first 10 chemicals).

with ChemicalDatabase() as db:
    try:
        print("\n" + "=" * 80)
        print("Chemical Database - Table View (First 10)")
        print("=" * 80)
        db.display_chemicals_table(limit=10)
    except Exception as e:
        print(f"Note: Could not display table format: {e}")


# %%
# # 8. View Detailed Information for a Chemical
# Display comprehensive information about a specific chemical.

with ChemicalDatabase() as db:
    try:
        print("\n" + "=" * 80)
        print("Detailed Information - CHLORINE")
        print("=" * 80)
        db.display_chemical_details("CHLORINE")
    except Exception as e:
        print(f"Note: Could not display details: {e}")


# %%
# # 9. Export to DataFrame (if pandas is available)
# Convert database to DataFrame format for advanced data analysis.

if HAS_PANDAS:
    try:
        with ChemicalDataFrame() as df_viewer:
            
            print("\n" + "=" * 80)
            print("Export to DataFrame - Chemicals with Molecular Weight < 50")
            print("=" * 80)
            
            # Filter by molecular weight
            filtered_df = df_viewer.filter_by_property('molecular_weight', max_value=50)
            print(f"\nFound {len(filtered_df)} chemicals with MW < 50:")
            print(filtered_df[['name', 'molecular_weight', 'cas_number']].head(10).to_string(index=False))
            
    except Exception as e:
        print(f"Error: {e}")
else:
    print("\n" + "=" * 80)
    print("Export to DataFrame")
    print("=" * 80)
    print("Note: pandas is not installed. Install it with: pip install pandas")


# %%
# # 10. Integration Pattern for Simulations
# Example of how to use the database in your own simulations or calculations.

def calculate_dispersion_parameters(chemical_name, release_rate_kg_per_s):
    """
    Example function showing how to integrate database access with simulations.
    
    Parameters:
    -----------
    chemical_name : str
        Name of the chemical
    release_rate_kg_per_s : float
        Release rate in kg/s
    
    Returns:
    --------
    dict : Properties needed for dispersion calculation
    """
    with ChemicalDatabase() as db:
        chem = db.get_chemical_by_name(chemical_name)
        
        if not chem:
            print(f"Error: Chemical '{chemical_name}' not found")
            return None
        
        # Extract properties for simulation
        sim_params = {
            'chemical_name': chem['name'],
            'molecular_weight': chem['molecular_weight'],
            'boiling_point_f': chem['ambient_boiling_point_f'],
            'idlh': chem['idlh'],
            'aegl3_60min': chem['aegl3_60min'],
            'release_rate': release_rate_kg_per_s,
        }
        
        return sim_params


# Run the integration example
print("\n" + "=" * 80)
print("Simulation Integration Pattern")
print("=" * 80)

params = calculate_dispersion_parameters("AMMONIA", 0.5)

if params:
    print(f"\nSimulation Parameters for {params['chemical_name']}:")
    print(f"Release Rate: {params['release_rate']} kg/s")
    print(f"\nChemical Properties:")
    for key, value in params.items():
        if key != 'chemical_name' and key != 'release_rate':
            print(f"  {key}: {value}")


# %%
# # Summary
# You've now explored the main features of the Chemical Database:
# 
# 1. **Basic Lookup** - Get chemical properties by name
# 2. **Search** - Find chemicals by partial name match
# 3. **CAS Lookup** - Find chemicals by CAS number
# 4. **Property Retrieval** - Extract specific properties
# 5. **Database Overview** - View statistics
# 6. **Available Properties** - See all property names
# 7. **Table Display** - View formatted chemical tables
# 8. **Detailed Info** - Get comprehensive chemical information
# 9. **DataFrame Export** - Advanced data manipulation with pandas
# 10. **Integration** - Use in your simulations
# 
# For more information, see `pyELDQM/data/chemicals_database/DATABASE_USAGE.md`

print("\n" + "=" * 80)
print("Tutorial Complete!")
print("=" * 80)