"""
Chemical Database Viewer with Pandas (Enhanced)

This module provides pandas-based viewing functions for better formatting.
Requires pandas to be installed: pip install pandas
"""

import pandas as pd
from pyeldqm.core.chemical_database import ChemicalDatabase
from typing import Optional


class ChemicalDataFrame:
    """Pandas-based viewer for the chemical database."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database connection."""
        self.db = ChemicalDatabase(db_path)
    
    def get_dataframe(self, limit: Optional[int] = None, 
                     search_term: Optional[str] = None) -> pd.DataFrame:
        """
        Get chemicals as a pandas DataFrame.
        
        Args:
            limit: Maximum number of chemicals to return
            search_term: Optional search term to filter chemicals
        
        Returns:
            pandas DataFrame with chemical data
        """
        if search_term:
            chemicals = self.db.search_chemicals(search_term)
            if limit:
                chemicals = chemicals[:limit]
        else:
            chemicals = self.db.get_all_chemicals(limit=limit)
        
        if not chemicals:
            return pd.DataFrame()
        
        return pd.DataFrame(chemicals)
    
    def view_table(self, limit: int = 20, search_term: Optional[str] = None,
                   columns: Optional[list] = None):
        """
        Display chemicals in a formatted pandas table.
        
        Args:
            limit: Maximum number of chemicals to display
            search_term: Optional search term to filter chemicals
            columns: List of columns to display (if None, shows key columns)
        """
        df = self.get_dataframe(limit=limit, search_term=search_term)
        
        if df.empty:
            print("No chemicals found.")
            return
        
        # Default columns if not specified
        if columns is None:
            columns = ['name', 'cas_number', 'molecular_weight', 'idlh', 
                      'ambient_boiling_point_f', 'lel', 'uel']
        
        # Filter to available columns
        columns = [col for col in columns if col in df.columns]
        
        # Display settings
        pd.set_option('display.max_rows', limit)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 40)
        
        print(f"\n{'='*100}")
        if search_term:
            print(f"Chemicals matching '{search_term}' ({len(df)} found, showing {limit})")
        else:
            print(f"Chemical Database ({len(df)} chemicals)")
        print(f"{'='*100}\n")
        
        print(df[columns].to_string(index=False))
        print(f"\n{'='*100}\n")
    
    def get_statistics(self) -> pd.DataFrame:
        """Get statistical summary of numerical properties."""
        df = self.get_dataframe()
        
        # Select numerical columns
        numerical_cols = ['molecular_weight', 'ambient_boiling_point_f', 
                         'freezing_point_f']
        numerical_cols = [col for col in numerical_cols if col in df.columns]
        
        return df[numerical_cols].describe()
    
    def export_to_csv(self, filename: str, limit: Optional[int] = None,
                     search_term: Optional[str] = None):
        """
        Export chemicals to CSV file.
        
        Args:
            filename: Output CSV filename
            limit: Maximum number of chemicals to export
            search_term: Optional search term to filter chemicals
        """
        df = self.get_dataframe(limit=limit, search_term=search_term)
        df.to_csv(filename, index=False)
        print(f"Exported {len(df)} chemicals to {filename}")
    
    def export_to_excel(self, filename: str, limit: Optional[int] = None,
                       search_term: Optional[str] = None):
        """
        Export chemicals to Excel file.
        
        Args:
            filename: Output Excel filename
            limit: Maximum number of chemicals to export
            search_term: Optional search term to filter chemicals
        """
        df = self.get_dataframe(limit=limit, search_term=search_term)
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"Exported {len(df)} chemicals to {filename}")
    
    def filter_by_property(self, property_name: str, min_value=None, 
                          max_value=None) -> pd.DataFrame:
        """
        Filter chemicals by property value range.
        
        Args:
            property_name: Name of the property to filter
            min_value: Minimum value (inclusive)
            max_value: Maximum value (inclusive)
        
        Returns:
            Filtered DataFrame
        """
        df = self.get_dataframe()
        
        if min_value is not None:
            df = df[df[property_name] >= min_value]
        if max_value is not None:
            df = df[df[property_name] <= max_value]
        
        return df
    
    def close(self):
        """Close database connection."""
        self.db.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Example usage
if __name__ == "__main__":
    try:
        import pandas as pd
        
        print("Enhanced Chemical Database Viewer (Pandas)")
        print("=" * 80)
        
        with ChemicalDataFrame() as viewer:
            # View chemicals table
            print("\n1. View first 15 chemicals:")
            viewer.view_table(limit=15)
            
            # Search and view
            print("\n2. Search for 'acid' chemicals:")
            viewer.view_table(limit=10, search_term='acid')
            
            # Get statistics
            print("\n3. Statistical Summary:")
            print(viewer.get_statistics())
            
            # Filter by molecular weight
            print("\n4. Light molecules (MW < 50):")
            df = viewer.filter_by_property('molecular_weight', max_value=50)
            print(df[['name', 'molecular_weight', 'ambient_boiling_point_f']].head(10))
            
            # Export example
            print("\n5. Export example:")
            viewer.export_to_csv('chemicals_export.csv', limit=100)
            
    except ImportError:
        print("Pandas is not installed. Install it with: pip install pandas")
        print("For Excel export, also install: pip install openpyxl")

