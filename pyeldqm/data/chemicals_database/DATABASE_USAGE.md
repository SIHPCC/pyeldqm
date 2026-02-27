# Chemical Database Usage Examples

This document shows how to access chemical properties from the `chemicals_database.sqlite3` file
located at `pyELDQM/data/chemicals_database/chemicals_database.sqlite3`.

## Basic Usage

```python
from pyELDQM.core.chemical_database import ChemicalDatabase

# Method 1: Using context manager (recommended - auto-closes connection)
with ChemicalDatabase() as db:
    # Get chemical by name
    ammonia = db.get_chemical_by_name("AMMONIA")
    print(ammonia['molecular_weight'])  # 17.03
    print(ammonia['idlh'])  # 300 ppm

# Method 2: Manual connection management
db = ChemicalDatabase()
chemical = db.get_chemical_by_name("CHLORINE")
print(chemical)
db.close()  # Remember to close!
```

## Available Methods

### 1. Get Chemical by Name
```python
with ChemicalDatabase() as db:
    chem = db.get_chemical_by_name("AMMONIA")
    if chem:
        print(f"MW: {chem['molecular_weight']}")
        print(f"Boiling Point: {chem['ambient_boiling_point_f']}°F")
```

### 2. Get Chemical by CAS Number
```python
with ChemicalDatabase() as db:
    chem = db.get_chemical_by_cas("7664-41-7")  # Ammonia
    print(chem['name'])
```

### 3. Search for Chemicals
```python
with ChemicalDatabase() as db:
    # Find all chemicals with "chlor" in the name
    results = db.search_chemicals("chlor")
    for chem in results:
        print(f"{chem['name']} - {chem['cas_number']}")
```

### 4. Get Specific Property
```python
with ChemicalDatabase() as db:
    # Get just one property
    mw = db.get_property("ACETONE", "molecular_weight")
    idlh = db.get_property("AMMONIA", "idlh")
```

### 5. Get All Chemicals
```python
with ChemicalDatabase() as db:
    all_chems = db.get_all_chemicals(limit=10)  # Get first 10
    # or
    all_chems = db.get_all_chemicals()  # Get all 807 chemicals
```

## Available Properties

Each chemical has the following properties:
- `id`: Database ID
- `name`: Chemical name
- `cas_number`: CAS registry number
- `molecular_weight`: Molecular weight (g/mol)
- `idlh`: Immediately Dangerous to Life or Health concentration
- `aegl1_60min`, `aegl2_60min`, `aegl3_60min`: Acute Exposure Guideline Levels
- `erpg1`, `erpg2`, `erpg3`: Emergency Response Planning Guidelines
- `pac1`, `pac2`, `pac3`: Protective Action Criteria
- `lel`: Lower Explosive Limit
- `uel`: Upper Explosive Limit
- `ambient_boiling_point_f`: Boiling point in Fahrenheit
- `freezing_point_f`: Freezing point in Fahrenheit
- `normal_boiling_point_f`: Normal boiling point in Fahrenheit

## Integration Example

```python
from pyELDQM.core.chemical_database import ChemicalDatabase

def calculate_dispersion(chemical_name, release_rate, ...):
    """Calculate dispersion with chemical properties from database."""
    
    with ChemicalDatabase() as db:
        # Get chemical properties
        chem = db.get_chemical_by_name(chemical_name)
        
        if not chem:
            raise ValueError(f"Chemical '{chemical_name}' not found in database")
        
        # Use properties in calculations
        mw = chem['molecular_weight']
        boiling_point = chem['ambient_boiling_point_f']
        
        # Your dispersion calculations here
        # ...
```

## Error Handling

```python
with ChemicalDatabase() as db:
    chem = db.get_chemical_by_name("UNKNOWN_CHEMICAL")
    
    if chem is None:
        print("Chemical not found!")
    else:
        # Use chemical properties
        pass
```

## Custom Database Path

```python
# If your database is in a different location
db = ChemicalDatabase(db_path="/path/to/your/database.sqlite3")
```
