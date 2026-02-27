# Chemical Database Viewing Guide

This guide shows you how to view and browse the chemical database in an organized way.

## Quick Start

### Method 1: Interactive Viewer (Recommended for browsing)

```bash
# Run the interactive viewer
python -m pyELDQM.view_database
```

This will give you a menu-driven interface to:
- View database summary
- Browse chemicals in table format
- Search for specific chemicals
- View detailed chemical properties

### Method 2: Direct Python Usage

```python
from pyELDQM.core.chemical_database import ChemicalDatabase

with ChemicalDatabase() as db:
    # Show database summary
    db.display_database_summary()
    
    # List all available properties
    db.list_available_properties()
    
    # Browse chemicals (table view)
    db.display_chemicals_table(limit=20)
    
    # Search for chemicals
    db.display_chemicals_table(search_term="acid", limit=15)
    
    # View detailed information
    db.display_chemical_details("AMMONIA")
```

## Display Functions

### 1. `display_database_summary()`
Shows overall database statistics:
- Total number of chemicals (807)
- Number with molecular weight data
- Number with IDLH values
- Database location

```python
db.display_database_summary()
```

Output:
```
================================================================================
Chemical Database Summary
================================================================================
📊 Total Chemicals:              807
⚖️  With Molecular Weight:        807
⚠️  With IDLH Values:             219
📁 Database Location:            pyELDQM/data/chemicals_database/chemicals_database.sqlite3
================================================================================
```

### 2. `list_available_properties()`
Shows all 19 properties available for each chemical:

```python
db.list_available_properties()
```

Properties include:
- Basic: name, CAS number, molecular weight
- Temperature: boiling point, freezing point
- Safety: IDLH, AEGL levels, ERPG levels, PAC levels
- Flammability: LEL, UEL

### 3. `display_chemicals_table(limit, search_term)`
Shows chemicals in a formatted table:

```python
# Show first 50 chemicals
db.display_chemicals_table(limit=50)

# Search for specific chemicals
db.display_chemicals_table(search_term="chlor", limit=20)
```

Table columns:
- Chemical Name
- CAS Number
- Molecular Weight (g/mol)
- IDLH
- Boiling Point (°F)

### 4. `display_chemical_details(chemical_name)`
Shows complete information for a specific chemical:

```python
db.display_chemical_details("AMMONIA")
db.display_chemical_details("CHLORINE")
```

Organized sections:
- 📋 Basic Properties (MW, CAS)
- 🌡️ Temperature Properties (BP, FP)
- 💥 Explosive Limits (LEL, UEL)
- ⚠️ Health Hazard Levels (IDLH, AEGL, ERPG, PAC)

## Advanced Usage with Pandas

For more advanced data analysis and export capabilities:

```python
from pyELDQM.core.chemical_dataframe import ChemicalDataFrame

with ChemicalDataFrame() as viewer:
    # Get data as pandas DataFrame
    df = viewer.get_dataframe(limit=100)
    
    # View with custom columns
    viewer.view_table(limit=20, columns=['name', 'molecular_weight', 'idlh'])
    
    # Get statistical summary
    stats = viewer.get_statistics()
    print(stats)
    
    # Filter by property value
    light_molecules = viewer.filter_by_property('molecular_weight', max_value=50)
    
    # Export to CSV or Excel
    viewer.export_to_csv('chemicals.csv')
    viewer.export_to_excel('chemicals.xlsx')  # requires openpyxl
```

## Common Use Cases

### Find chemicals by name
```python
with ChemicalDatabase() as db:
    db.display_chemicals_table(search_term="ammonia")
```

### Browse all toxic gases
```python
with ChemicalDatabase() as db:
    db.display_chemicals_table(search_term="gas", limit=30)
```

### View safety information
```python
with ChemicalDatabase() as db:
    db.display_chemical_details("CHLORINE")
    # Shows IDLH, AEGL, ERPG, PAC levels
```

### Get specific property values
```python
with ChemicalDatabase() as db:
    # Still available - get just one property
    mw = db.get_property("AMMONIA", "molecular_weight")
    idlh = db.get_property("CHLORINE", "idlh")
    print(f"Ammonia MW: {mw}, Chlorine IDLH: {idlh}")
```

## Tips

1. **Case-insensitive search**: Chemical names are matched case-insensitively
2. **Partial matching**: Search terms match partial names (e.g., "chlor" finds "CHLORINE", "CHLOROFORM", etc.)
3. **Data availability**: Some properties may be NULL/N/A for certain chemicals
4. **Export data**: Use the pandas viewer for exporting to CSV/Excel
5. **Interactive mode**: Use `view_database.py` for guided browsing

## Requirements

Basic viewer (no extra dependencies):
```bash
# Already included with pyELDQM
```

Enhanced pandas viewer:
```bash
pip install pandas
pip install openpyxl  # For Excel export
```

## Examples

### Example 1: Find all acids
```python
with ChemicalDatabase() as db:
    db.display_chemicals_table(search_term="acid", limit=20)
```

### Example 2: Check hazardous materials
```python
with ChemicalDatabase() as db:
    chemicals = ["AMMONIA", "CHLORINE", "SULFUR DIOXIDE", "HYDROGEN SULFIDE"]
    for chem in chemicals:
        db.display_chemical_details(chem)
```

### Example 3: Export filtered data
```python
from pyELDQM.core.chemical_dataframe import ChemicalDataFrame

with ChemicalDataFrame() as viewer:
    # Get only low-boiling chemicals
    df = viewer.filter_by_property('ambient_boiling_point_f', max_value=100)
    df.to_csv('low_boiling_chemicals.csv', index=False)
```
