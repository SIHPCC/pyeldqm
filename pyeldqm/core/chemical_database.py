"""
Chemical Database Access Module

This module provides easy access to chemical properties from the SQLite database.
"""

import sqlite3
import os
import sys
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


def _find_chemicals_db() -> str:
    """
    Locate chemicals_database.sqlite3 in order of preference:
    1. Source-tree path relative to this file  (editable installs, dev runs)
    2. importlib.resources inside the installed ``pyeldqm.data.chemicals_database`` package
       (non-editable / wheel installs)
    3. Raise a clear FileNotFoundError with troubleshooting guidance.
    """
    # --- 1. Source-tree / editable install ---
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_path = os.path.join(
        base_dir, "data", "chemicals_database", "chemicals_database.sqlite3"
    )
    if os.path.exists(source_path):
        return source_path

    # --- 2. importlib.resources (wheel / non-editable install) ---
    try:
        import importlib.resources as pkg_resources  # Python ≥ 3.9

        ref = pkg_resources.files("pyeldqm.pyeldqm.data.chemicals_database").joinpath(
            "chemicals_database.sqlite3"
        )
        resolved = str(ref)
        if os.path.exists(resolved):
            return resolved
    except Exception:
        pass

    # --- 3. Friendly error ---
    raise FileNotFoundError(
        f"Cannot locate chemicals_database.sqlite3.\n"
        f"  Searched: {source_path}\n"
        f"  To fix this, reinstall the package in editable mode from the source tree:\n"
        f"      pip install -e \".[full]\"\n"
        f"  or, for conda users:\n"
        f"      conda activate pyeldqm\n"
        f"      pip install -e \".[full]\""
    )


class ChemicalDatabase:
    """Interface to access chemical properties from the SQLite database."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the chemical database connection.
        
        Args:
            db_path: Path to the SQLite database. If None, uses default path.
        """
        if db_path is None:
            db_path = _find_chemicals_db()
        
        self.db_path = db_path
        self._conn = None
    
    def _get_connection(self):
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row  # Enable dict-like access
        return self._conn
    
    def get_chemical_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get chemical properties by name.
        
        Args:
            name: Chemical name (case-insensitive)
        
        Returns:
            Dictionary with chemical properties or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM shanto_chemical WHERE LOWER(name) = LOWER(?)",
            (name,)
        )
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_chemical_by_cas(self, cas_number: str) -> Optional[Dict[str, Any]]:
        """
        Get chemical properties by CAS number.
        
        Args:
            cas_number: CAS registry number
        
        Returns:
            Dictionary with chemical properties or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM shanto_chemical WHERE cas_number = ?",
            (cas_number,)
        )
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def search_chemicals(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for chemicals by partial name match.
        
        Args:
            search_term: Partial name to search for (case-insensitive)
        
        Returns:
            List of matching chemicals
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM shanto_chemical WHERE LOWER(name) LIKE LOWER(?)",
            (f'%{search_term}%',)
        )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_chemicals(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all chemicals from database.
        
        Args:
            limit: Maximum number of results to return
        
        Returns:
            List of all chemicals
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM shanto_chemical ORDER BY name"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_property(self, chemical_name: str, property_name: str) -> Optional[Any]:
        """
        Get a specific property value for a chemical.
        
        Args:
            chemical_name: Name of the chemical
            property_name: Name of the property (e.g., 'molecular_weight', 'idlh')
        
        Returns:
            Property value or None if not found
        """
        chemical = self.get_chemical_by_name(chemical_name)
        if chemical:
            return chemical.get(property_name)
        return None
    
    def get_database_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics about the database.
        
        Returns:
            Dictionary with database statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM shanto_chemical")
        total_count = cursor.fetchone()[0]
        
        # Get chemicals with molecular weight
        cursor.execute("SELECT COUNT(*) FROM shanto_chemical WHERE molecular_weight IS NOT NULL")
        mw_count = cursor.fetchone()[0]
        
        # Get chemicals with IDLH values
        cursor.execute("SELECT COUNT(*) FROM shanto_chemical WHERE idlh IS NOT NULL")
        idlh_count = cursor.fetchone()[0]
        
        return {
            'total_chemicals': total_count,
            'with_molecular_weight': mw_count,
            'with_idlh': idlh_count,
            'database_path': self.db_path
        }
    
    def display_chemicals_table(self, limit: int = 20, search_term: Optional[str] = None):
        """
        Display chemicals in a formatted table with all available properties.
        
        Args:
            limit: Maximum number of chemicals to display
            search_term: Optional search term to filter chemicals
        """
        if search_term:
            chemicals = self.search_chemicals(search_term)[:limit]
            print(f"\n{'='*200}")
            print(f"Chemicals matching '{search_term}' (showing {min(len(chemicals), limit)} of {len(chemicals)})")
            print(f"{'='*200}")
        else:
            chemicals = self.get_all_chemicals(limit=limit)
            total = self.get_database_summary()['total_chemicals']
            print(f"\n{'='*200}")
            print(f"Chemical Database (showing {min(len(chemicals), limit)} of {total} total chemicals)")
            print(f"{'='*200}")
        
        if not chemicals:
            print("No chemicals found.")
            return
        
        # Get all column names from the database
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(shanto_chemical)")
        columns_info = cursor.fetchall()
        
        # Extract column names (excluding 'id' as it's internal)
        all_properties = [col[1] for col in columns_info if col[1] != 'id']
        
        # Define column widths for better display
        column_widths = {
            'name': 30,
            'cas_number': 12,
            'molecular_weight': 10,
            'idlh': 10,
            'aegl1_60min': 12,
            'aegl2_60min': 12,
            'aegl3_60min': 12,
            'erpg1': 10,
            'erpg2': 10,
            'erpg3': 10,
            'pac1': 10,
            'pac2': 10,
            'pac3': 10,
            'lel': 10,
            'uel': 10,
            'ambient_boiling_point_f': 12,
            'freezing_point_f': 12,
            'normal_boiling_point_f': 12
        }
        
        # Print header with all properties
        header_parts = []
        for prop in all_properties:
            width = column_widths.get(prop, 15)
            # Format property name for display (convert underscores to spaces, title case)
            display_name = prop.replace('_', ' ').title()
            if len(display_name) > width:
                display_name = display_name[:width-2] + '..'
            header_parts.append(f"{display_name:<{width}}")
        
        header = " ".join(header_parts)
        total_width = len(header)
        print(header)
        print("-" * total_width)
        
        # Print rows with all properties
        for chem in chemicals:
            row_parts = []
            for prop in all_properties:
                width = column_widths.get(prop, 15)
                value = chem.get(prop)
                
                # Format value based on type and property
                if value is None:
                    formatted_value = 'N/A'
                elif prop == 'name':
                    # Truncate long names
                    formatted_value = (value[:width-3] + '...') if len(value) > width else value
                elif prop == 'molecular_weight':
                    formatted_value = f"{value:.2f}"
                elif prop in ['ambient_boiling_point_f', 'freezing_point_f', 'normal_boiling_point_f']:
                    formatted_value = f"{value:.1f}"
                elif isinstance(value, (int, float)):
                    formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                else:
                    formatted_value = str(value)
                    if len(formatted_value) > width:
                        formatted_value = formatted_value[:width-2] + '..'
                
                row_parts.append(f"{formatted_value:<{width}}")
            
            print(" ".join(row_parts))
        
        print("=" * total_width)
    
    def display_chemical_details(self, chemical_name: str):
        """
        Display detailed information about a specific chemical.
        
        Args:
            chemical_name: Name of the chemical to display
        """
        chem = self.get_chemical_by_name(chemical_name)
        
        if not chem:
            print(f"\nChemical '{chemical_name}' not found in database.")
            return
        
        print(f"\n{'='*80}")
        print(f"Chemical Details: {chem['name']}")
        print(f"{'='*80}")
        
        # Basic properties
        print("\n📋 Basic Properties:")
        print(f"  CAS Number:        {chem['cas_number'] or 'N/A'}")
        print(f"  Molecular Weight:  {chem['molecular_weight'] or 'N/A'} g/mol")
        
        # Temperature properties
        print("\n🌡️  Temperature Properties:")
        print(f"  Boiling Point:     {chem['ambient_boiling_point_f'] or 'N/A'} °F")
        print(f"  Freezing Point:    {chem['freezing_point_f'] or 'N/A'} °F")
        
        # Explosive limits
        print("\n💥 Explosive Limits:")
        print(f"  LEL:               {chem['lel'] or 'N/A'}")
        print(f"  UEL:               {chem['uel'] or 'N/A'}")
        
        # Health hazard levels
        print("\n⚠️  Health Hazard Levels:")
        print(f"  IDLH:              {chem['idlh'] or 'N/A'}")
        
        print("\n  AEGL (60 min):")
        print(f"    Level 1:         {chem['aegl1_60min'] or 'N/A'}")
        print(f"    Level 2:         {chem['aegl2_60min'] or 'N/A'}")
        print(f"    Level 3:         {chem['aegl3_60min'] or 'N/A'}")
        
        print("\n  ERPG:")
        print(f"    Level 1:         {chem['erpg1'] or 'N/A'}")
        print(f"    Level 2:         {chem['erpg2'] or 'N/A'}")
        print(f"    Level 3:         {chem['erpg3'] or 'N/A'}")
        
        print("\n  PAC:")
        print(f"    Level 1:         {chem['pac1'] or 'N/A'}")
        print(f"    Level 2:         {chem['pac2'] or 'N/A'}")
        print(f"    Level 3:         {chem['pac3'] or 'N/A'}")
        
        print(f"\n{'='*80}\n")
    
    def display_database_summary(self):
        """Display summary statistics about the database."""
        summary = self.get_database_summary()
        
        print(f"\n{'='*80}")
        print("Chemical Database Summary")
        print(f"{'='*80}")
        print(f"📊 Total Chemicals:              {summary['total_chemicals']}")
        print(f"⚖️  With Molecular Weight:        {summary['with_molecular_weight']}")
        print(f"⚠️  With IDLH Values:             {summary['with_idlh']}")
        print(f"📁 Database Location:            {summary['database_path']}")
        print(f"{'='*80}\n")
    
    def list_available_properties(self):
        """Display all available properties in the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(shanto_chemical)")
        columns = cursor.fetchall()
        
        print(f"\n{'='*80}")
        print("Available Chemical Properties")
        print(f"{'='*80}")
        
        for i, col in enumerate(columns, 1):
            col_name = col[1]
            col_type = col[2]
            print(f"{i:2}. {col_name:<30} ({col_type})")
        
        print(f"{'='*80}\n")
    
    def export_to_csv(self, filepath: str) -> bool:
        """
        Export all chemicals and their properties to a CSV file.
        
        Args:
            filepath: Path where the CSV file will be saved
        
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            import csv
            
            # Get all chemicals
            chemicals = self.get_all_chemicals(limit=None)
            
            if not chemicals:
                print("No chemicals to export.")
                return False
            
            # Get all property names from the first chemical
            fieldnames = list(chemicals[0].keys())
            
            # Write to CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for chem in chemicals:
                    # Convert None values to 'N/A' for better readability
                    row = {}
                    for field in fieldnames:
                        value = chem.get(field)
                        if value is None:
                            row[field] = 'N/A'
                        else:
                            row[field] = value
                    writer.writerow(row)
            
            return True
        
        except Exception as e:
            logger.exception("Error exporting to CSV: %s", e)
            return False
    
    def __del__(self) -> None:
        """Ensure the SQLite connection is closed on garbage collection."""
        self.close()

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Example usage
if __name__ == "__main__":
    print("Chemical Database Viewer")
    print("=" * 80)
    
    with ChemicalDatabase() as db:
        # Display database summary
        db.display_database_summary()
        
        # List all available properties
        db.list_available_properties()
        
        # Display chemicals table (first 20)
        db.display_chemicals_table(limit=20)
        
        # Search for specific chemicals
        print("\n" + "=" * 80)
        db.display_chemicals_table(limit=10, search_term="chlor")
        
        # Display detailed information for a specific chemical
        db.display_chemical_details("AMMONIA")
        db.display_chemical_details("CHLORINE")
        
        print("\n💡 Usage Examples:")
        print("  db.display_database_summary()           # Show database stats")
        print("  db.list_available_properties()          # List all properties")
        print("  db.display_chemicals_table(limit=50)    # Show 50 chemicals")
        print("  db.display_chemicals_table(search_term='acid')  # Search chemicals")
        print("  db.display_chemical_details('AMMONIA')  # Show full details")


