"""
Live Loop Manager for Real-time Monitoring Applications

Provides a universal manager for live monitoring loops with:
- Automatic cycle counting and timing
- Browser auto-open on first cycle
- Countdown timers with progress display
- Error handling and retry logic
- Graceful shutdown with statistics
"""

import time
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable


class LiveLoopManager:
    """
    Universal manager for real-time monitoring loops.
    
    Handles cycle counting, browser management, countdown timers,
    error handling, and graceful shutdown for live monitoring applications.
    
    Example:
    --------
    >>> manager = LiveLoopManager(
    ...     update_interval=60,
    ...     output_file=Path("output.html"),
    ...     app_name="Threat Zone Monitor"
    ... )
    >>> 
    >>> for cycle in manager.run():
    ...     # Your monitoring logic here
    ...     weather = get_weather()
    ...     concentration = calculate_dispersion(weather)
    ...     map_obj = create_map(concentration)
    ...     map_obj.save(str(manager.output_file))
    ...     manager.open_browser_once()  # Auto-opens on first cycle
    ...     manager.wait_for_next_cycle()  # Countdown timer
    """
    
    def __init__(
        self,
        update_interval: int = 60,
        output_file: Optional[Path] = None,
        app_name: str = "pyELDQM Monitor"
    ):
        """
        Initialize the live loop manager.
        
        Parameters:
        -----------
        update_interval : int
            Seconds between updates (default: 60)
        output_file : Path, optional
            Path to output HTML file for browser auto-open
        app_name : str
            Application name for display messages
        """
        self.update_interval = update_interval
        self.output_file = output_file
        self.app_name = app_name
        
        # State tracking
        self.cycle_count = 0
        self.browser_opened = False
        self.start_time = None
        self.last_update_time = None
        
    def run(self):
        """
        Main monitoring loop generator.
        
        Yields cycle numbers and handles KeyboardInterrupt for graceful shutdown.
        
        Yields:
        -------
        int : Current cycle number
        """
        self.start_time = datetime.now()
        
        try:
            while True:
                self.cycle_count += 1
                self.last_update_time = datetime.now()
                
                # Print cycle header
                print(f"\n{'='*90}")
                print(f"UPDATE CYCLE #{self.cycle_count} - {self.last_update_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*90}")
                
                yield self.cycle_count
                
        except KeyboardInterrupt:
            self._print_shutdown_summary()
    
    def open_browser_once(self):
        """
        Open browser on first cycle only.
        
        Automatically opens the output file in the default browser
        on the first monitoring cycle. Subsequent calls do nothing.
        """
        if self.browser_opened or not self.output_file:
            return
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Opening map in browser...")
        try:
            webbrowser.open(f'file:///{self.output_file}')
            self.browser_opened = True
            print(f"  ✓ Browser opened successfully")
            print(f"  ✓ Refresh browser (F5) to see latest updates")
        except Exception as e:
            print(f"  Note: Could not auto-open browser: {e}")
            print(f"  Please open manually: {self.output_file}")
            self.browser_opened = True
    
    def wait_for_next_cycle(self):
        """
        Wait for the next update cycle with countdown display.
        
        Shows a countdown timer that updates every 10 seconds
        to inform the user of remaining time.
        """
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Next update in {self.update_interval}s...")
        print("(Press Ctrl+C to stop, F5 in browser to refresh)")
        
        for i in range(self.update_interval):
            time.sleep(1)
            if i % 10 == 0 and i > 0:
                remaining = self.update_interval - i
                print(f"  [{remaining}s remaining...]", end='\r')
        
        print(" " * 40, end='\r')  # Clear countdown
    
    def handle_error(self, error: Exception):
        """
        Handle errors during monitoring cycle.
        
        Prints error information and waits before retry.
        
        Parameters:
        -----------
        error : Exception
            The exception that occurred
        """
        print(f"\n✗ Error in update cycle: {error}")
        import traceback
        traceback.print_exc()
        print(f"  Retrying in {self.update_interval}s...")
        time.sleep(self.update_interval)
    
    def _print_shutdown_summary(self):
        """Print summary statistics on graceful shutdown."""
        print(f"\n\n{'='*90}")
        print(f"{self.app_name.upper()} STOPPED BY USER")
        print(f"{'='*90}")
        print(f"Total updates completed: {self.cycle_count}")
        
        if self.start_time:
            duration = datetime.now() - self.start_time
            hours, remainder = divmod(int(duration.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"Total runtime: {hours}h {minutes}m {seconds}s")
        
        if self.output_file:
            print(f"Final map saved to: {self.output_file}")
        
        print(f"\nThank you for using {self.app_name}")
        print(f"{'='*90}\n")


def create_live_loop(
    update_interval: int = 60,
    output_file: Optional[Path] = None,
    app_name: str = "pyELDQM Monitor"
) -> LiveLoopManager:
    """
    Factory function to create a LiveLoopManager instance.
    
    Parameters:
    -----------
    update_interval : int
        Seconds between updates (default: 60)
    output_file : Path, optional
        Path to output HTML file
    app_name : str
        Application name for display
    
    Returns:
    --------
    LiveLoopManager
        Configured manager instance
    """
    return LiveLoopManager(
        update_interval=update_interval,
        output_file=output_file,
        app_name=app_name
    )
